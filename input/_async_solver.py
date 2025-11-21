"""
Async solver with event handling.
"""

from __future__ import annotations
import asyncio
import inspect
import json
import os
import sys
from typing import Callable, Any, IO, final, Awaitable
from typing_extensions import TypedDict
from ._model import Model
from ._serialization import serialize_to_json
from ._solver import SolveResult, ObjectiveEntry, LowerBoundEntry
from ._solution import Solution
from ._parameters import Parameters


# Import version for handshake
from . import __version__


# === Event Types ============================================================

@final
class SolutionEvent(TypedDict, total=False):
    """
    Event emitted when a solution is found during solving.

    This event is passed to the on_solution callback and contains:
    - The solution object with variable values
    - The solve time when the solution was found
    - Optional validation status if solution verification is enabled
    """
    solveTime: float
    """Duration of the solve at the time the solution was found, in seconds."""

    valid: bool
    """
    Result of solution verification (only present if Parameters.verifySolutions is True).

    When solution verification is enabled (default), the solver independently verifies
    that all constraints are satisfied and the objective is computed correctly.
    If present, the value is always True (solver would error if verification failed).
    """

    solution: Solution
    """The solution containing values for all variables and the objective value."""


@final
class SolveSummary(TypedDict, total=False):
    """
    Summary statistics from the solver at completion.

    This is the data sent in the final 'summary' message from the solver
    and passed to the on_summary callback. Contains aggregate statistics
    about the entire solve including search statistics, resource usage,
    and environment information.

    All fields are optional (total=False) as the exact set of fields may
    vary depending on solver version and problem type.
    """
    # Core results
    nbSolutions: int
    """Total number of solutions found."""

    proof: bool
    """Whether the solve ended with a proof (optimality or infeasibility)."""

    duration: float
    """Total duration of the solve in seconds."""

    # Search statistics
    nbBranches: int
    """Total number of branches explored."""

    nbFails: int
    """Total number of failures encountered."""

    nbLNSSteps: int
    """Total number of Large Neighborhood Search steps."""

    nbRestarts: int
    """Total number of restarts performed."""

    # Resource usage
    memoryUsed: int
    """Memory used by the solver in bytes."""

    # Objective information
    objective: float | list[float | None]
    """Best objective value found (for optimization problems)."""

    lowerBound: float | list[float | None]
    """Proved lower bound on the objective (for minimization problems)."""

    objectiveSense: str
    """Objective direction: "minimize", "maximize", or None for satisfaction problems."""

    # Model statistics
    nbIntVars: int
    """Number of integer variables in the model (after preprocessing)."""

    nbIntervalVars: int
    """Number of interval variables in the model (after preprocessing)."""

    nbConstraints: int
    """Number of constraints in the model (after preprocessing)."""

    # Environment information
    solver: str
    """Solver name and version string (e.g., "OptalCP 2025.8.0")."""

    nbWorkers: int
    """Number of worker threads used during solving."""

    cpu: str
    """CPU name detected by the solver."""


def _enable_windows_ansi() -> bool:
    """
    Enable ANSI escape sequences on Windows.

    Returns:
        True if ANSI mode was enabled or already supported, False otherwise
    """
    if sys.platform != 'win32':
        return True  # Not Windows, assume ANSI is supported

    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # Get handle to stdout
        handle = kernel32.GetStdHandle(-11)
        # Enable VIRTUAL_TERMINAL_PROCESSING (0x0004) | DISABLE_NEWLINE_AUTO_RETURN (0x0008)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            mode.value |= 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
            return bool(kernel32.SetConsoleMode(handle, mode))
    except Exception:
        pass

    return False


def _can_use_colors(output_stream: IO[str] | None) -> bool:
    """
    Detect if ANSI color codes can be used in output.

    Checks multiple conditions to determine color support:
    - NO_COLOR environment variable (disables colors if set)
    - FORCE_COLOR environment variable (forces colors if set)
    - Jupyter/IPython environments (VS Code notebooks, JupyterLab, etc.)
    - TTY detection for terminal output
    - Windows ANSI support

    Args:
        output_stream: The output stream to check (e.g., sys.stdout)

    Returns:
        True if ANSI colors can be used, False otherwise

    References:
        - NO_COLOR standard: https://no-color.org/
        - FORCE_COLOR: Common convention for CI/CD and logging
    """
    # Respect NO_COLOR standard: https://no-color.org/
    if os.environ.get('NO_COLOR'):
        return False

    # Force colors if requested (useful for CI/CD, logging)
    if os.environ.get('FORCE_COLOR'):
        return True

    # No stream = no colors
    if output_stream is None:
        return False

    # Detect Jupyter/IPython environments (VS Code notebooks, JupyterLab, Jupyter Classic, etc.)
    # These environments support ANSI colors even though they're not TTYs
    try:
        from IPython import get_ipython # type: ignore[import]
        if get_ipython() is not None:
            # We're running in a Jupyter kernel - colors work!
            return True
    except ImportError:
        # IPython not installed, not in Jupyter
        pass

    # Check if output stream is a TTY (traditional terminal check)
    if hasattr(output_stream, 'isatty') and output_stream.isatty():
        # On Windows, try to enable ANSI support
        if sys.platform == 'win32':
            return _enable_windows_ansi()
        return True

    # No color support detected
    return False


def _find_solver_path() -> str:
    """
    Find the path to the optalcp solver executable.

    Checks in order:
    1. OPTALCP_SOLVER environment variable (override)
    2. optalcp-bin package (full edition) - priority 1
    3. optalcp-bin-academic package - priority 2
    4. optalcp-bin-preview package - priority 3
    5. optalcp in PATH

    Returns:
        Path to the solver executable

    Raises:
        FileNotFoundError: If solver cannot be found

    Remarks:
        This function mirrors the JavaScript solver discovery logic from
        npm-packages/optalcp/input/api.ts:2045-2067. If multiple binary
        packages are installed, the full edition takes priority over academic,
        which takes priority over preview.
    """
    # 1. Check environment variable first (override)
    solver_path = os.environ.get('OPTALCP_SOLVER')
    if solver_path:
        if os.path.isfile(solver_path) and os.access(solver_path, os.X_OK):
            return solver_path
        else:
            raise FileNotFoundError(
                f"OPTALCP_SOLVER points to invalid executable: {solver_path}"
            )

    # 2. Try optalcp-bin (full edition) - priority 1
    try:
        import optalcp_bin
        return str(optalcp_bin.get_solver_path())
    except ImportError:
        pass
    except Exception:
        pass  # Binary not available for this platform

    # 3. Try optalcp-bin-academic - priority 2
    try:
        import optalcp_bin_academic
        return str(optalcp_bin_academic.get_solver_path())
    except ImportError:
        pass
    except Exception:
        pass

    # 4. Try optalcp-bin-preview - priority 3
    try:
        import optalcp_bin_preview
        return str(optalcp_bin_preview.get_solver_path())
    except ImportError:
        pass
    except Exception:
        pass

    # 5. Try to find optalcp in PATH
    import shutil
    solver_path = shutil.which('optalcp')
    if solver_path:
        return solver_path

    # Not found
    raise FileNotFoundError(
        "OptalCP solver not found. Install with:\n"
        "  pip install git+https://github.com/ScheduleOpt/optalcp-py-bin-preview@latest\n"
        "Or set OPTALCP_SOLVER environment variable, or ensure 'optalcp' is in your PATH."
    )


# TODO-DOC-NEEDS-UPDATE: Solver.md documents JavaScript EventEmitter-based API, Python uses callback properties instead
class Solver:
    """#doc[Solver]

    Python-specific implementation notes:

    Unlike the JavaScript API which uses EventEmitter, the Python Solver uses callback properties:
    - output_stream: Where to write log/warning messages (default: sys.stdout)
    - on_log, on_warning, on_error: Callbacks for message events
    - on_solution, on_lower_bound, on_summary: Callbacks for solve events

    Example with default output to stdout:
        solver = Solver()
        result = await solver.solve(model)  # Logs and warnings go to stdout

    Example with redirected output:
        with open('solver.log', 'w', encoding='utf-8') as f:
            solver = Solver(output_stream=f)
            result = await solver.solve(model)  # Logs and warnings go to file

    Example to disable output:
        solver = Solver(output_stream=None)
        result = await solver.solve(model)  # No output

    Example with custom event handlers:
        solver = Solver(
            on_log=lambda msg: my_logger.info(msg),
            on_warning=lambda msg: my_logger.warning(msg)
        )
        result = await solver.solve(model)

    Example changing output stream and callbacks after instantiation:
        solver = Solver()
        solver.output_stream = sys.stderr  # Redirect to stderr
        solver.on_log = lambda msg: print(f"LOG: {msg}")  # Add log handler
        result = await solver.solve(model)

    Example collecting solutions with callback modification:
        solver = Solver(output_stream=None)
        solutions = []

        def collect_solution(event):
            solutions.append(event['solution'])
            print(f"Found solution at {event['solveTime']:.2f}s")

        solver.on_solution = collect_solution
        result = await solver.solve(model)
        print(f"Collected {len(solutions)} solutions")
    """

    @property
    def output_stream(self) -> IO[str] | None:
        """
        Stream where log and warning messages are written.

        Can be set to any file-like object (file, sys.stdout, sys.stderr, etc.)
        or None to disable output. Messages are written to this stream before
        calling the corresponding callbacks (on_log, on_warning).

        Example:
            ```python
            solver = Solver()
            solver.output_stream = sys.stderr  # Redirect to stderr
            solver.output_stream = None  # Disable output
            ```
        """
        return self._output_stream

    @output_stream.setter
    def output_stream(self, value: IO[str] | None) -> None:
        self._output_stream = value

    @property
    def on_log(self) -> Callable[[str], None] | Callable[[str], Awaitable[None]] | None:
        """
        Callback function for log messages from the solver.

        Called AFTER the log message is written to output_stream.
        Set to None to disable (default). Can be either a synchronous or asynchronous function.

        Args (callback signature):
            msg (str): The log message text.

        Example:
            ```python
            solver = Solver()
            solver.on_log = lambda msg: my_logger.info(msg)
            # or:
            def log_handler(msg: str) -> None:
                print(f"LOG: {msg}")
            solver.on_log = log_handler
            # or async:
            async def async_log_handler(msg: str) -> None:
                await async_logger.info(msg)
            solver.on_log = async_log_handler
            ```
        """
        return self._on_log

    @on_log.setter
    def on_log(self, value: Callable[[str], None] | Callable[[str], Awaitable[None]] | None) -> None:
        self._on_log = value

    @property
    def on_warning(self) -> Callable[[str], None] | Callable[[str], Awaitable[None]] | None:
        """
        Callback function for warning messages from the solver.

        Called AFTER the warning is written to output_stream.
        Set to None to disable (default). Can be either a synchronous or asynchronous function.

        Args (callback signature):
            msg (str): The warning message text.

        Example:
            ```python
            solver = Solver()
            solver.on_warning = lambda msg: warnings.warn(msg)
            # or async:
            async def async_warning_handler(msg: str) -> None:
                await async_logger.warning(msg)
            solver.on_warning = async_warning_handler
            ```
        """
        return self._on_warning

    @on_warning.setter
    def on_warning(self, value: Callable[[str], None] | Callable[[str], Awaitable[None]] | None) -> None:
        self._on_warning = value

    @property
    def on_error(self) -> Callable[[str], None] | Callable[[str], Awaitable[None]] | None:
        """
        Callback function for error messages from the solver.

        Called for each error message. Errors are also written to sys.stderr.
        Set to None to disable (default). Can be either a synchronous or asynchronous function.

        Note: Errors from the solver are typically non-fatal (e.g., "parameter
        not supported in academic edition"). Fatal errors raise RuntimeError.

        Args (callback signature):
            msg (str): The error message text.

        Example:
            ```python
            solver = Solver()
            solver.on_error = lambda msg: print(f"ERROR: {msg}", file=sys.stderr)
            # or async:
            async def async_error_handler(msg: str) -> None:
                await async_logger.error(msg)
            solver.on_error = async_error_handler
            ```
        """
        return self._on_error

    @on_error.setter
    def on_error(self, value: Callable[[str], None] | Callable[[str], Awaitable[None]] | None) -> None:
        self._on_error = value

    @property
    def on_solution(self) -> Callable[[SolutionEvent], None] | Callable[[SolutionEvent], Awaitable[None]] | None:
        """
        Callback function for solution events from the solver.

        Called each time the solver finds a new solution.
        Set to None to disable (default). Can be either a synchronous or asynchronous function.

        Args (callback signature):
            event (SolutionEvent): Dictionary with keys:
                - 'solution' (Solution): The solution object with variable values
                - 'solveTime' (float): Time when solution was found (seconds)
                - 'valid' (bool, optional): Verification result if enabled

        Example:
            ```python
            def handle_solution(event: cp.SolutionEvent) -> None:
                sol = event['solution']
                time = event['solveTime']
                print(f"Solution found at {time:.2f}s, objective={sol.get_objective()}")

            solver = Solver()
            solver.on_solution = handle_solution

            # or async:
            async def async_handle_solution(event: cp.SolutionEvent) -> None:
                sol = event['solution']
                await save_to_database(sol)

            solver.on_solution = async_handle_solution
            ```

        See Also:
            SolutionEvent: TypedDict defining the event structure
        """
        return self._on_solution

    @on_solution.setter
    def on_solution(self, value: Callable[[SolutionEvent], None] | Callable[[SolutionEvent], Awaitable[None]] | None) -> None:
        self._on_solution = value

    @property
    def on_lower_bound(self) -> Callable[[LowerBoundEntry], None] | Callable[[LowerBoundEntry], Awaitable[None]] | None:
        """
        Callback function for lower bound events from the solver.

        Called when the solver improves the lower bound on the objective.
        Set to None to disable (default). Can be either a synchronous or asynchronous function.

        Args (callback signature):
            event (LowerBoundEntry): Dictionary with keys:
                - 'value' (float | list): The new lower bound value
                - 'solveTime' (float): Time when bound was proved (seconds)

        Example:
            ```python
            solver = Solver()
            solver.on_lower_bound = lambda event: print(f"LB: {event['value']}")
            # or async:
            async def async_lb_handler(event: cp.LowerBoundEntry) -> None:
                await update_dashboard(event['value'])
            solver.on_lower_bound = async_lb_handler
            ```

        See Also:
            LowerBoundEntry: TypedDict defining the event structure
        """
        return self._on_lower_bound

    @on_lower_bound.setter
    def on_lower_bound(self, value: Callable[[LowerBoundEntry], None] | Callable[[LowerBoundEntry], Awaitable[None]] | None) -> None:
        self._on_lower_bound = value

    @property
    def on_summary(self) -> Callable[[SolveSummary], None] | Callable[[SolveSummary], Awaitable[None]] | None:
        """
        Callback function for solve completion event.

        Called once when the solve completes, providing final statistics.
        Set to None to disable (default). Can be either a synchronous or asynchronous function.

        Args (callback signature):
            summary (SolveSummary): Dictionary with solve statistics including:
                - 'nbSolutions' (int): Number of solutions found
                - 'duration' (float): Total solve time in seconds
                - 'nbBranches' (int): Number of branches explored
                - 'objective' (float, optional): Best objective value
                - Plus many other statistics (see SolveSummary)

        Example:
            ```python
            def handle_summary(summary: cp.SolveSummary) -> None:
                print(f"Solve completed: {summary['nbSolutions']} solutions")
                print(f"Time: {summary['duration']:.2f}s")

            solver = Solver()
            solver.on_summary = handle_summary

            # or async:
            async def async_handle_summary(summary: cp.SolveSummary) -> None:
                await save_stats_to_db(summary)

            solver.on_summary = async_handle_summary
            ```

        See Also:
            SolveSummary: TypedDict defining the summary structure
        """
        return self._on_summary

    @on_summary.setter
    def on_summary(self, value: Callable[[SolveSummary], None] | Callable[[SolveSummary], Awaitable[None]] | None) -> None:
        self._on_summary = value

    def __init__(self) -> None:
        """
        Create a solver instance.

        Callbacks and output stream can be configured after instantiation
        using the properties: output_stream, on_log, on_warning, on_error,
        on_solution, on_lower_bound, on_summary.

        Example:
            ```python
            solver = Solver()
            solver.output_stream = None  # Disable output
            solver.on_solution = lambda event: print(f"Found solution!")
            result = await solver.solve(model)
            ```
        """
        # Initialize output stream and callbacks to default values
        self._output_stream = sys.stdout
        self._on_log = None
        self._on_warning = None
        self._on_error = None
        self._on_solution = None
        self._on_lower_bound = None
        self._on_summary = None

        self._process: asyncio.subprocess.Process | None = None
        self._stop_requested = False
        self._best_solution: Solution | None = None
        self._solutions: list[Solution] = []
        self._objective_history: list[ObjectiveEntry] = []
        self._lower_bound_history: list[LowerBoundEntry] = []
        self._best_solution_time: float | None = None
        self._best_lb_time: float | None = None
        self._best_solution_valid: bool | None = None
        self._task_group: asyncio.TaskGroup | None = None

    def _call_handler(self, handler: Callable[..., Any] | None, *args: Any) -> None:
        """
        Call a handler function, which may be sync or async, without blocking.

        For async handlers, creates a task within the task group that runs concurrently.
        Sync handlers are called immediately. This matches the TypeScript EventEmitter
        behavior where emit() doesn't block on handlers.

        Args:
            handler: The callback function (sync or async), or None
            *args: Arguments to pass to the handler
        """
        if handler is None:
            return

        if inspect.iscoroutinefunction(handler):
            # Async handler - create task in group (automatically tracked and cleaned up)
            if self._task_group is not None:
                self._task_group.create_task(handler(*args))
        else:
            # Sync handler - call directly
            handler(*args)

    async def _readline_unbounded(self, reader: asyncio.StreamReader) -> bytes:
        """
        Read a line from the reader, recovering from buffer overflow.

        If the line exceeds the buffer limit, this method will catch the
        LimitOverrunError and read the data in chunks until the newline is found.

        This allows the solver to handle arbitrarily large JSON messages even
        when pythonStreamBufferSize is set to a small value.

        Args:
            reader: The asyncio StreamReader to read from

        Returns:
            The complete line including the newline character
        """
        chunks: list[bytes] = []
        while True:
            try:
                # Use readuntil() instead of readline() to avoid ValueError conversion
                line = await reader.readuntil(b'\n')
                # If we have accumulated chunks, prepend them
                if chunks:
                    return b''.join(chunks) + line
                return line
            except asyncio.LimitOverrunError as e:
                # Data stays in buffer - read what we have so far
                chunk = await reader.readexactly(e.consumed)
                chunks.append(chunk)
                # Loop continues to find the newline

    async def solve(self,
                    model: Model,
                    params: Parameters | None = None,
                    warm_start: Solution | None = None) -> SolveResult:
        """#doc[Solver.solve]"""
        # Reset stop flag and solutions
        self._stop_requested = False
        self._best_solution = None
        self._solutions = []
        self._objective_history = []
        self._lower_bound_history = []
        self._best_solution_time = None
        self._best_lb_time = None
        self._best_solution_valid = None
        self._task_group = None

        # Detect color support based on initial output_stream
        self._colors = _can_use_colors(self._output_stream)

        # Find solver
        self._solver_path = _find_solver_path()

        # Prepare model data
        model_data = model._to_dict()
        model_data['msg'] = 'solve'

        # Add parameters if specified
        if params:
            model_data['parameters'] = params._to_dict()

        # Add warm start if specified
        if warm_start:
            model_data['warmStart'] = warm_start._to_dict()

        # Serialize model to JSON
        json_bytes = serialize_to_json(model_data)

        # Write to file if OPTALCP_MODEL is set (for debugging)
        model_file = os.environ.get('OPTALCP_MODEL')
        if model_file:
            try:
                with open(model_file, 'wb') as f:
                    f.write(json_bytes)
                print(f"Model file '{model_file}' written successfully.")
            except Exception as e:
                print(f"Warning: Cannot write model file '{model_file}': {e}")

        # Start solver subprocess
        try:
            buffer_size = params.pythonStreamBufferSize if params else 2*1024*1024
            self._process = await asyncio.create_subprocess_exec(
                self._solver_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=buffer_size
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start solver: {e}") from e
        assert self._process.stdin is not None
        assert self._process.stdout is not None
        assert self._process.stderr is not None

        try:
            # Send handshake
            handshake: dict[str, Any] = {"msg": "handshake", "version": __version__, "colors": self._colors}
            handshake_bytes = serialize_to_json(handshake) + b'\n'
            self._process.stdin.write(handshake_bytes)
            await self._process.stdin.drain()

            # Read handshake response
            handshake_response = await self._readline_unbounded(self._process.stdout)
            if not handshake_response:
                raise RuntimeError("Solver closed unexpectedly during handshake")

            # Parse handshake response
            try:
                handshake_data = json.loads(handshake_response)
                if handshake_data.get('msg') != 'handshake':
                    raise RuntimeError(f"Unexpected handshake response: {handshake_data}")
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Invalid handshake response: {e}")

            # Send solve message
            solve_bytes = json_bytes + b'\n'
            self._process.stdin.write(solve_bytes)
            # Note: No need to drain() here - stdin will flush asynchronously while we
            # start reading from stdout. The solver will read when ready.
            # Also, do not close stdin here - we may need to send additional messages
            # (e.g., solutions via send_solution()) during the solve

            # A wrapper to capture summary data from _process_messages in outer scope
            summary_data = None
            async def run_process_messages():
                nonlocal summary_data
                summary_data = await self._process_messages()

            # Use TaskGroup to manage async handler tasks such as user's async callbacks
            # Also run _process_messages() as a task so any exception in callbacks
            # (async or sync) will immediately cancel message processing (and all tasks in the group)
            async with asyncio.TaskGroup() as tg:
                self._task_group = tg

                # Run message processing as a task in the group
                tg.create_task(run_process_messages())

            # TaskGroup automatically waits for all tasks to complete here
            # Reset task group to None so no new tasks can be created
            self._task_group = None

            # Wait for process to finish
            return_code = await self._process.wait()

            if return_code != 0:
                stderr = await self._process.stderr.read()
                stderr_text = stderr.decode('utf-8', errors='replace')
                raise RuntimeError(
                    f"Solver failed with return code {return_code}.\n"
                    f"STDERR: {stderr_text}"
                )

            if summary_data is None:
                raise RuntimeError("Solver did not return a summary message")

            return SolveResult(
                summary_data,
                self._best_solution,
                self._solutions,
                self._objective_history,
                self._lower_bound_history,
                self._best_solution_time,
                self._best_lb_time,
                self._best_solution_valid
            )

        except Exception as e:
            # Kill process if still running
            if self._process.returncode is None:
                self._process.kill()
                await self._process.wait()
            raise

    def stop(self, reason: str = "User requested") -> None:
        """#doc[Solver.stop]"""
        # No process running or already finished
        if self._process is None or self._process.returncode is not None:
            return

        # Second call to stop - kill immediately as a safety measure
        if self._stop_requested:
            self._process.kill()
            return

        # stdin not available - can't send graceful stop, so kill
        if self._process.stdin is None or self._process.stdin.is_closing():
            self._process.kill()
            self._stop_requested = True
            return

        # First call - try graceful stop
        try:
            stop_msg = {"msg": "stop", "reason": reason}
            stop_bytes = serialize_to_json(stop_msg) + b'\n'
            self._process.stdin.write(stop_bytes)
            self._stop_requested = True
            # Note: We don't await drain() here because we might not be in async context
        except Exception:
            # If we can't send stop message, kill the process
            self._process.kill()
            self._stop_requested = True

    async def send_solution(self, solution: Solution) -> None:
        """#doc[Solver.sendSolution]"""
        # Check if solver is running and stdin is available
        if self._process is None:
            return  # Solver not started yet
        if self._process.returncode is not None:
            return  # Solver has finished
        if self._process.stdin is None or self._process.stdin.is_closing():
            return  # stdin not available

        # Send solution message
        try:
            message: dict[str, Any] = {"msg": "solution", "data": solution._to_dict()}
            await self._send_message(message)
        except Exception:
            # Solver may have died while sending - ignore
            pass

    async def _send_message(self, message: dict[str, Any]) -> None:
        """
        Send a JSON message to the solver.

        Args:
            message: Dictionary to send as JSON.

        Note:
            This function writes to the buffer and returns immediately without waiting
            for the data to be flushed (no drain). This matches the TypeScript behavior
            where messages are sent asynchronously.
        """
        if self._process is None or self._process.stdin is None:
            return

        try:
            message_bytes = serialize_to_json(message) + b'\n'
            self._process.stdin.write(message_bytes)
            # No drain() - message will be flushed asynchronously
        except Exception:
            # If writing fails, the solver has likely terminated
            pass

    async def _process_messages(self) -> dict[str, Any] | None:
        """
        Read and process messages from solver until summary is received.

        Returns:
            Summary data dict, or None if no summary received
        """
        assert self._process is not None
        assert self._process.stdout is not None
        summary_data = None

        while True:
            line = await self._readline_unbounded(self._process.stdout)
            if not line:
                # EOF reached
                break

            # Parse JSON message
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                # Skip non-JSON lines
                continue

            msg_type = message.get('msg')
            data = message.get('data')

            # Handle log messages: write to output_stream, then call handler
            if msg_type == 'log':
                if self.output_stream is not None:
                    self.output_stream.write(data)
                    self.output_stream.flush()

                self._call_handler(self.on_log, data)

            # Handle warning messages: write to output_stream, then call handler
            elif msg_type == 'warning':
                if self.output_stream is not None:
                    prefix = message.get('prefix', '')
                    warning_text = f"{prefix}{data}"
                    self.output_stream.write(warning_text)
                    self.output_stream.flush()

                # Pass the message itself
                self._call_handler(self.on_warning, data)

            elif msg_type == 'error':
                # Always write errors to stderr (Python convention for errors)
                sys.stderr.write(data)
                sys.stderr.flush()

                # Then call user callback if provided
                self._call_handler(self.on_error, data)

            elif msg_type == 'solution':
                # Parse solution from data
                solution = Solution()
                solution._init_from_dict(data)

                # Store as best solution and add to solutions list
                self._best_solution = solution
                self._solutions.append(solution)

                # Track in objective history
                history_item: ObjectiveEntry = {
                    'solveTime': data.get('solveTime', 0.0),
                    'objective': solution.get_objective() or 0.0,
                    'valid': data.get('verifiedOK', True)
                }
                self._objective_history.append(history_item)

                # Track best solution metadata
                self._best_solution_time = data.get('solveTime')
                if 'verifiedOK' in data:
                    self._best_solution_valid = data['verifiedOK']

                # Call user handler with Solution object
                # Create solution event dict similar to TypeScript API
                event: SolutionEvent = {
                    'solveTime': data.get('solveTime'),
                    'solution': solution
                }
                # Only include 'valid' if verification was performed
                if 'verifiedOK' in data:
                    event['valid'] = data['verifiedOK']

                self._call_handler(self.on_solution, event)

            elif msg_type == 'lowerBound':
                # Track in lower bound history
                lb_event: LowerBoundEntry = {
                    'solveTime': data.get('solveTime', 0.0),
                    'value': data.get('value', 0.0)
                }
                self._lower_bound_history.append(lb_event)
                self._best_lb_time = data.get('solveTime')

                # Call user callback if provided
                self._call_handler(self.on_lower_bound, data)

            elif msg_type == 'summary':
                summary_data = data

                # Call on_summary callback if provided
                self._call_handler(self.on_summary, summary_data)

                # Summary is the last message, we can stop
                break

        return summary_data
