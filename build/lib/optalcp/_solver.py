"""
Unified solver with both sync and async capabilities.

This module provides the Solver class which supports:
- Synchronous solving via _sync_solve() (used by Model.solve())
- Asynchronous solving via solve() with callback support
"""

from __future__ import annotations
import asyncio
import inspect
import json
import os
import signal
import subprocess
import sys
from typing import Callable, Any, IO, final, Awaitable
from typing_extensions import TypedDict, NotRequired
from ._model import Model
from ._serialization import serialize_to_json
from ._result import SolveResult, ObjectiveEntry, LowerBoundEntry, SolveSummary, _RawSolveSummary
from ._solution import Solution
from ._parameters import Parameters
from ._utils import _can_use_colors, _find_solver_path


# Import version for handshake
from . import __version__


# === Event Types ============================================================

@final
class SolutionEvent(TypedDict):
    """
    Event emitted when a solution is found during solving.

    This event is passed to the on_solution callback and contains:
    - The solution object with variable values
    - The solve time when the solution was found
    - Optional validation status if solution verification is enabled
    """
    solveTime: float
    """Duration of the solve at the time the solution was found, in seconds."""

    valid: NotRequired[bool]
    """
    Result of solution verification (only present if Parameters.verifySolutions is True).

    When solution verification is enabled (default), the solver independently verifies
    that all constraints are satisfied and the objective is computed correctly.
    If present, the value is always True (solver would error if verification failed).
    """

    solution: Solution
    """The solution containing values for all variables and the objective value."""


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

        The callback receives a SolveSummary instance with snake_case property access
        for Pythonic API consistency.

        Args (callback signature):
            summary (SolveSummary): Solve statistics with properties including:
                - nb_solutions (int): Number of solutions found
                - duration (float): Total solve time in seconds
                - nb_branches (int): Number of branches explored
                - objective (float | None): Best objective value
                - Plus many other statistics (see SolveSummary)

        Example:
            ```python
            def handle_summary(summary: cp.SolveSummary) -> None:
                print(f"Solve completed: {summary.nb_solutions} solutions")
                print(f"Time: {summary.duration:.2f}s")

            solver = Solver()
            solver.on_summary = handle_summary

            # or async:
            async def async_handle_summary(summary: cp.SolveSummary) -> None:
                await save_stats_to_db(summary)

            solver.on_summary = async_handle_summary
            ```

        See Also:
            SolveSummary: Class defining the summary structure
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
        self._colors = False
        self._solver_path = ""
        self._solution: Solution | None = None
        self._solutions: list[Solution] = []
        self._objective_history: list[ObjectiveEntry] = []
        self._lower_bound_history: list[LowerBoundEntry] = []
        self._solution_time: float | None = None
        self._best_lb_time: float | None = None
        self._solution_valid: bool | None = None
        self._errors: list[str] = []
        self._stderr_output: list[str] = []
        self._closing = False
        self._task_group: asyncio.TaskGroup | None = None
        self._keyboard_interrupt_count = 0
        self._raw_summary_data: _RawSolveSummary | None = None
        self._text_result: str | None = None

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
            The complete line including the newline character, or empty bytes on EOF
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
            except asyncio.IncompleteReadError:
                # EOF reached before finding newline - return empty bytes to signal EOF
                return b''

    async def _run(self,
                   command: str,
                   model: Model,
                   params: Parameters | None = None,
                   warm_start: Solution | None = None) -> None:
        """
        Run a command against the solver subprocess.

        This is the core communication method shared by solve(), _to_text(), etc.
        Results are stored in instance variables:
        - _raw_summary_data: For 'solve' command
        - _text_result: For 'toText' and 'toJS' commands
        - _solution, _solutions, etc.: For solution tracking

        Args:
            command: The command to send ('solve', 'toText', 'toJS')
            model: The model to process
            params: Optional solver parameters
            warm_start: Optional initial solution
        """
        self._reset_state()

        # Prepare command data (shared with sync version)
        json_bytes = self._prepare_command(command, model, params, warm_start)

        # Set up SIGINT (Ctrl-C) handler
        # When Ctrl-C is pressed, the terminal sets SIGINT for the whole process
        # group. So both the parent Python process and the solver subprocess
        # receive SIGINT. And solver reacts by stopping gracefully. However:
        #  * On windows, only Python process receives SIGINT
        #  * If SIGINT is sent specifically to the Python process by `kill -INT <pid>`,
        #    only Python receives it (even on Linux).
        # So we ALWAYS call stop() on first Ctrl-C to inform the solver.
        original_sigint_handler = signal.getsignal(signal.SIGINT)

        def sigint_handler(signum: int, frame: Any) -> None:
            self._keyboard_interrupt_count += 1
            if self._keyboard_interrupt_count == 1:
                # First Ctrl-C: suppress KeyboardInterrupt and stop solver gracefully
                self.stop("Interrupted")
            else:
                # Second Ctrl-C: restore original handler and kill immediately
                signal.signal(signal.SIGINT, original_sigint_handler)
                # Raise KeyboardInterrupt to kill the process
                raise KeyboardInterrupt()

        signal.signal(signal.SIGINT, sigint_handler)

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
            # Send handshake (shared preparation with sync version)
            handshake_bytes = self._prepare_handshake(self._colors)
            self._process.stdin.write(handshake_bytes)
            await self._process.stdin.drain()

            # Read and validate handshake response (shared parsing with sync version)
            handshake_response = await self._readline_unbounded(self._process.stdout)
            self._parse_handshake_response(handshake_response)

            # Send command message
            self._process.stdin.write(json_bytes)
            # Note: No need to drain() here - stdin will flush asynchronously while we
            # start reading from stdout. The solver will read when ready.
            # Also, do not close stdin here - we may need to send additional messages
            # (e.g., solutions via send_solution()) during the solve

            # Use TaskGroup to manage async handler tasks such as user's async callbacks
            # Also run _process_messages() and _read_stderr() as tasks so any exception
            # will immediately cancel all tasks in the group
            async with asyncio.TaskGroup() as tg:
                self._task_group = tg
                tg.create_task(self._process_messages())
                tg.create_task(self._read_stderr())

            # TaskGroup automatically waits for all tasks to complete here
            # Reset task group to None so no new tasks can be created
            self._task_group = None

            # Wait for process to finish (with timeout)
            timeout_sec = params.processExitTimeout if params and params.processExitTimeout is not None else 3.0
            try:
                await asyncio.wait_for(self._process.wait(), timeout=timeout_sec)
            except asyncio.TimeoutError:
                self._process.kill()
                await self._process.wait()

            # Check if stderr had output (indicates solver crash/error)
            if self._stderr_output:
                stderr_text = '\n'.join(self._stderr_output)
                raise RuntimeError(f"Solver error:\n{stderr_text}")

            # Check if we accumulated errors during solving
            if self._errors:
                error_summary = '\n'.join(self._errors)
                raise RuntimeError(
                    f"Solver reported error(s):\n{error_summary}"
                )

            return_code = self._process.returncode
            if return_code != 0:
                raise RuntimeError(
                    f"Solver failed with return code {return_code}."
                )

        except Exception:
            # Kill process if still running
            if self._process.returncode is None:
                self._process.kill()
                await self._process.wait()
            raise

        finally:
            # Restore original SIGINT handler
            signal.signal(signal.SIGINT, original_sigint_handler)

    async def solve(self,
                    model: Model,
                    params: Parameters | None = None,
                    warm_start: Solution | None = None) -> SolveResult:
        r"""
        Solves a given model with the given parameters.

        :param model: The model to solve
        :type model: Model
        :param params: The parameters for the solver
        :type params: Parameters
        :param warmStart: An initial solution to start the solver with
        :type warmStart: Solution
        :param log: A stream to redirect the solver output to. If null, the output is suppressed. If undefined, the output stream is not changed (the default is standard output)
        :type log: NodeJS.WritableStream | null

        :returns: A promise that resolves to a SolveResult object when the solve is finished.
        :rtype: Promise<SolveResult>

        The solving process starts asynchronously. Use `await` to wait for the
        solver to finish.  During the solve, the solver emits events that can be
        intercepted (see :meth:`Solver.on`) to execute a code when the event occurs.

        Note that JavaScript is single-threaded.  Therefore, it cannot communicate
        with the solver subprocess while the user code runs.  The user code
        must be idle (using `await` or waiting for an event) for the solver to
        function correctly.

        ### Warm start and external solutions

        If the `warmStart` parameter is specified, the solver will start with the
        given solution.  The solution must be compatible with the model; otherwise
        an error is raised.  The solver will take advantage of the
        solution to speed up the search: it will search only for better solutions
        (if it is a minimization or maximization problem). The solver may try to
        improve the provided solution by Large Neighborhood Search.

        There are two ways to pass a solution to the solver: using `warmStart`
        parameter and using function :meth:`Solver.send_solution`.
        The difference is that `warmStart` is guaranteed to be used by the solver
        before the solve starts.  On the other hand, `send_solution` can be called
        at any time during the solve.

        Parameter :meth:`Parameters.LNSUseWarmStartOnly` controls whether the
        solver should only use the warm start solution (and not search for other
        initial solutions).
        """
        await self._run("solve", model, params, warm_start)

        if self._raw_summary_data is None:
            raise RuntimeError("Solver did not return a summary message")

        # Build and return SolveResult from stored data
        return SolveResult(
            self._raw_summary_data,
            self._solution,
            self._solutions,
            self._objective_history,
            self._lower_bound_history,
            self._solution_time,
            self._best_lb_time,
            self._solution_valid
        )

    async def _to_text(self,
                       command: str,
                       model: Model,
                       params: Parameters | None = None,
                       warm_start: Solution | None = None) -> str:
        """
        Convert model to text format using the specified command.

        Args:
            command: Either 'toText' or 'toJS'
            model: The model to convert
            params: Optional solver parameters
            warm_start: Optional initial solution

        Returns:
            The text representation of the model
        """
        await self._run(command, model, params, warm_start)

        if self._text_result is None:
            raise RuntimeError("Solver did not return a textModel message")

        return self._text_result

    def stop(self, reason: str = "User requested") -> None:
        r"""
        Instruct the solver to stop ASAP.

        :param reason: The reason why to stop. The reason will appear in the log
        :type reason: string

        :returns: A promise that resolves when the solver has stopped
        :rtype: Promise<void>

        A stop message is sent to the server asynchronously. The server will
        stop as soon as possible and will send a summary event and close event.
        However, due to the asynchronous nature of the communication,
        other events may be sent before the summary event (e.g., another solution
        found or a log message).

        Requesting a stop on a solver that has already stopped has no effect.

        In the following example, we issue a stop command 1 minute after the first
        solution is found.
        """
        # No process running or already finished
        if self._process is None or self._process.returncode is not None:
            return

        # Second call to stop - kill immediately as a safety measure
        if self._stop_requested:
            self._process.kill()
            return

        # Try graceful stop via _send_message (returns silently if can't send)
        self._send_message({"msg": "stop", "reason": reason})
        self._stop_requested = True

    async def send_solution(self, solution: Solution) -> None:
        r"""
        Send an external solution to the solver.

        :param solution: The solution to send. It must be compatible with the model; otherwise, an error is raised
        :type solution: Solution

        :returns: A promise that resolves when the solution has been sent
        :rtype: Promise<void>

        This function can be used to send an external solution to the solver, e.g.
        found by another solver, a heuristic, or a user.  The solver will take
        advantage of the solution to speed up the search: it will search only for
        better solutions (if it is a minimization or maximization problem). The
        solver may try to improve the provided solution by Large Neighborhood
        Search.

        The solution does not have to be better than the current best solution
        found by the solver. It is up to the solver whether or not it will use the
        solution in this case.

        Sending a solution to a solver that has already stopped has no effect.

        The solution is sent to the solver asynchronously. Unless parameter
        :meth:`Parameters.logLevel` is set to 0, the solver will log a message when it
        receives the solution.
        """
        self._send_message({"msg": "solution", "data": solution._to_dict()})

    def _send_message(self, message: dict[str, Any]) -> None:
        """
        Send a JSON message to the solver. Returns silently if solver not running.

        Args:
            message: Dictionary to send as JSON.

        Note:
            This function writes to the buffer and returns immediately without waiting
            for the data to be flushed (no drain). This matches the TypeScript behavior
            where messages are sent asynchronously.
        """
        if self._process is None or self._process.stdin is None:
            return
        if self._process.returncode is not None:
            return
        if self._process.stdin.is_closing():
            return

        message_bytes = serialize_to_json(message) + b'\n'
        self._process.stdin.write(message_bytes)
        # No drain() - message will be flushed asynchronously

    async def _process_messages(self) -> None:
        """
        Read and process messages from solver until completion (async version).

        Uses _handle_message() for processing which supports async callbacks
        via _task_group.
        """
        assert self._process is not None
        assert self._process.stdout is not None

        while True:
            line = await self._readline_unbounded(self._process.stdout)
            if not line:
                # EOF - check if expected (we already received summary/textModel/errors/stderr)
                if not self._raw_summary_data and not self._text_result and not self._errors and not self._stderr_output:
                    raise RuntimeError("Solver closed unexpectedly without sending results")
                break

            if not self._handle_message(line):
                break

    async def _read_stderr(self) -> None:
        """
        Read stderr from solver concurrently with stdout.

        Any output on stderr indicates a solver error. The content is collected
        in _stderr_output and also echoed to sys.stderr immediately.
        """
        assert self._process is not None and self._process.stderr is not None

        while True:
            line = await self._process.stderr.readline()
            if not line:
                break
            text = line.decode('utf-8', errors='replace')
            sys.stderr.write(text)
            sys.stderr.flush()
            self._stderr_output.append(text.rstrip('\n'))

    # =========================================================================
    # Public conversion methods (async versions of Model methods)
    # =========================================================================

    async def to_json(self,
                      model: Model,
                      params: Parameters | None = None,
                      warm_start: Solution | None = None) -> str:
        r"""
        Exports a model to JSON format (async version).

        :param model: The model to export
        :type model: Model
        :param params: Optional solver parameters to include
        :type params: Parameters
        :param warm_start: Optional initial solution to include
        :type warm_start: Solution

        :returns: A string containing the model in JSON format.
        :rtype: string

        Async version of :meth:`to_json`. This method performs JSON
        serialization locally without requiring solver communication.

        .. rubric:: Example

        .. code-block:: python

            import asyncio
            import optalcp as cp

            async def export_model():
                model = cp.Model()
                x = model.interval_var(length=10, name="task_x")
                model.minimize(x.end())

                solver = cp.Solver()
                json_str = await solver.to_json(model)
                return json_str

            json_str = asyncio.run(export_model())

        .. seealso::

            - :meth:`to_json` for synchronous usage.
            - :meth:`from_json` to import from JSON.
        """
        # JSON serialization is local - doesn't require solver communication
        from ._result import _to_json_impl
        return _to_json_impl(model, params, warm_start)

    async def to_txt(self,
                     model: Model,
                     params: Parameters | None = None,
                     warm_start: Solution | None = None) -> str:
        r"""
        Converts a model to text format (async version).

        :param model: The model to convert
        :type model: Model
        :param params: Optional solver parameters
        :type params: Parameters
        :param warm_start: Optional initial solution to include
        :type warm_start: Solution

        :returns: Text representation of the model.
        :rtype: string

        Async version of :meth:`to_txt`. This method communicates with
        the solver process to generate the text output.

        The output is human-readable and similar to the IBM CP Optimizer file format.

        .. rubric:: Example

        .. code-block:: python

            import asyncio
            import optalcp as cp

            async def export_model():
                model = cp.Model()
                x = model.interval_var(length=10, name="task_x")
                model.minimize(x.end())

                solver = cp.Solver()
                solver.output_stream = None  # Suppress solver output
                text = await solver.to_txt(model)
                return text

            text = asyncio.run(export_model())
            print(text)

        .. seealso::

            - :meth:`to_txt` for synchronous usage.
            - :meth:`to_js` for JavaScript export.
        """
        return await self._to_text("toText", model, params, warm_start)

    async def to_js(self,
                    model: Model,
                    params: Parameters | None = None,
                    warm_start: Solution | None = None) -> str:
        r"""
        Converts a model to JavaScript code (async version).

        :param model: The model to convert
        :type model: Model
        :param params: Optional solver parameters (included in generated code)
        :type params: Parameters
        :param warm_start: Optional initial solution to include
        :type warm_start: Solution

        :returns: JavaScript code representing the model.
        :rtype: string

        Async version of :meth:`to_js`. This method communicates with
        the solver process to generate the JavaScript output.

        The output is human-readable, executable with Node.js, and can be stored
        in a file.

        This feature is experimental and the result is not guaranteed to be valid
        in all cases.

        .. rubric:: Example

        .. code-block:: python

            import asyncio
            import optalcp as cp

            async def export_model():
                model = cp.Model()
                x = model.interval_var(length=10, name="task_x")
                model.minimize(x.end())

                solver = cp.Solver()
                solver.output_stream = None  # Suppress solver output
                js_code = await solver.to_js(model)
                return js_code

            js_code = asyncio.run(export_model())
            print(js_code)

        .. seealso::

            - :meth:`to_js` for synchronous usage.
            - :meth:`to_txt` for text format export.
        """
        return await self._to_text("toJS", model, params, warm_start)

    # =========================================================================
    # Shared helper methods (used by both sync and async solving)
    # =========================================================================

    def _reset_state(self) -> None:
        """Reset solver state before a new solve/conversion operation."""
        self._stop_requested = False
        self._solution = None
        self._solutions = []
        self._objective_history = []
        self._lower_bound_history = []
        self._solution_time = None
        self._best_lb_time = None
        self._solution_valid = None
        self._errors = []
        self._stderr_output = []
        self._closing = False
        self._task_group = None
        self._keyboard_interrupt_count = 0
        self._raw_summary_data = None
        self._text_result = None

    def _prepare_command(self,
                         command: str,
                         model: Model,
                         params: Parameters | None,
                         warm_start: Solution | None) -> bytes:
        """
        Prepare solver command data (shared by sync and async).

        Sets self._colors and self._solver_path as side effects.

        Returns:
            JSON bytes to send to solver (with trailing newline)
        """
        # Detect color support and find solver path
        self._colors = _can_use_colors(self._output_stream)
        self._solver_path = _find_solver_path()

        # Prepare model data
        model_data = model._to_dict()
        model_data['msg'] = command

        if params:
            model_data['parameters'] = params._to_dict()

        if warm_start:
            model_data['warmStart'] = warm_start._to_dict()

        json_bytes = serialize_to_json(model_data)

        # Write model to file if OPTALCP_MODEL is set (for debugging)
        model_file = os.environ.get('OPTALCP_MODEL')
        if model_file:
            try:
                with open(model_file, 'wb') as f:
                    f.write(json_bytes)
                print(f"Model file '{model_file}' written successfully.")
            except Exception as e:
                print(f"Warning: Cannot write model file '{model_file}': {e}")

        return json_bytes + b'\n'

    def _parse_handshake_response(self, response: bytes) -> None:
        """Parse and validate handshake response from solver."""
        if not response:
            raise RuntimeError("Solver closed unexpectedly during handshake")

        try:
            handshake_data = json.loads(response)
            if handshake_data.get('msg') != 'handshake':
                raise RuntimeError(f"Unexpected handshake response: {handshake_data}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid handshake response: {e}")

    def _prepare_handshake(self, colors: bool) -> bytes:
        """Prepare handshake message bytes to send to solver."""
        handshake: dict[str, Any] = {
            "msg": "handshake", "version": __version__, "colors": colors}
        return serialize_to_json(handshake) + b'\n'

    def _handle_message(self, line: bytes) -> bool:
        """
        Process a single message from the solver.

        Parses JSON and updates internal state. In async mode (_task_group is set),
        async callbacks are scheduled as tasks. In sync mode, only sync callbacks are called.

        Args:
            line: Raw bytes from solver stdout (JSON message)

        Returns:
            True to continue processing messages, False if this is the final message

        Raises:
            RuntimeError: If the line is not valid JSON
        """
        try:
            message: dict[str, Any] = json.loads(line)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON from solver: {e}")

        msg_type = message.get('msg')
        data: Any = message.get('data')

        # Handle error first - allowed even after terminal message
        if msg_type == 'error':
            prefix = message.get('prefix', '')
            error_text = f"{prefix}{data}"
            sys.stderr.write(error_text)
            sys.stderr.flush()
            if data is not None:
                self._errors.append(data)
            self._call_handler(self.on_error, data)
            return True

        # After terminal message (summary/textModel), only error messages are allowed
        if self._closing:
            raise RuntimeError(f"Unexpected output after terminal message: {line[:100]!r}")

        if msg_type == 'log':
            if self.output_stream is not None and data is not None:
                self.output_stream.write(data)
                self.output_stream.flush()
            self._call_handler(self.on_log, data)
            return True

        if msg_type == 'warning':
            if self.output_stream is not None and data is not None:
                prefix = message.get('prefix', '')
                warning_text = f"{prefix}{data}"
                self.output_stream.write(warning_text)
                self.output_stream.flush()
            self._call_handler(self.on_warning, data)
            return True

        if msg_type == 'solution' and data is not None:
            solution = Solution()
            solution._init_from_dict(data)
            self._solution = solution
            self._solutions.append(solution)

            history_item: ObjectiveEntry = {
                'solveTime': data['solveTime'],
                'objective': solution.get_objective()
            }
            if 'verifiedOK' in data:
                history_item['valid'] = data['verifiedOK']
            self._objective_history.append(history_item)

            self._solution_time = data['solveTime']
            if 'verifiedOK' in data:
                self._solution_valid = data['verifiedOK']

            event: SolutionEvent = {
                'solveTime': data['solveTime'],
                'solution': solution
            }
            if 'verifiedOK' in data:
                event['valid'] = data['verifiedOK']
            self._call_handler(self.on_solution, event)
            return True

        if msg_type == 'lowerBound' and data is not None:
            lb_event: LowerBoundEntry = {
                'solveTime': data['solveTime'],
                'value': data['value']
            }
            self._lower_bound_history.append(lb_event)
            self._best_lb_time = data['solveTime']
            self._call_handler(self.on_lower_bound, data)
            return True

        if msg_type == 'textModel':
            self._text_result = data
            self._closing = True  # Terminal message - only errors allowed after this
            return True  # Continue reading until EOF

        if msg_type == 'summary' and data is not None:
            self._raw_summary_data = data
            user_summary = SolveSummary(data)
            self._call_handler(self.on_summary, user_summary)
            self._closing = True  # Terminal message - only errors allowed after this
            return True  # Continue reading until EOF

        raise RuntimeError(f"Unknown message type from solver: {msg_type}")

    def _sync_run(self,
                  command: str,
                  model: Model,
                  params: Parameters | None = None,
                  warm_start: Solution | None = None) -> None:
        """
        Run a command against the solver subprocess (synchronous version).

        Uses subprocess.Popen for blocking I/O. This is used internally by
        Model.solve(), Model.to_txt(), and Model.to_js().

        Args:
            command: The command to send ('solve', 'toText', 'toJS')
            model: The model to process
            params: Optional solver parameters
            warm_start: Optional initial solution
        """
        self._reset_state()

        # Prepare command data (shared with async version)
        json_bytes = self._prepare_command(command, model, params, warm_start)

        # Set up SIGINT handler for graceful interruption
        original_sigint_handler = signal.getsignal(signal.SIGINT)
        sync_process: subprocess.Popen[bytes] | None = None

        def sigint_handler(signum: int, frame: Any) -> None:
            self._keyboard_interrupt_count += 1
            if self._keyboard_interrupt_count == 1:
                # First Ctrl-C: try graceful stop
                if sync_process is not None and sync_process.stdin is not None:
                    try:
                        stop_msg = {"msg": "stop", "reason": "Interrupted"}
                        stop_bytes = serialize_to_json(stop_msg) + b'\n'
                        sync_process.stdin.write(stop_bytes)
                        sync_process.stdin.flush()
                    except Exception:
                        # Can't send graceful stop - kill the process
                        if sync_process.returncode is None:
                            sync_process.kill()
                elif sync_process is not None and sync_process.returncode is None:
                    # stdin not available - kill the process
                    sync_process.kill()
            else:
                # Second Ctrl-C: restore handler and raise
                signal.signal(signal.SIGINT, original_sigint_handler)
                raise KeyboardInterrupt()

        signal.signal(signal.SIGINT, sigint_handler)

        try:
            # Start solver subprocess
            sync_process = subprocess.Popen(
                [self._solver_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            assert sync_process.stdin is not None
            assert sync_process.stdout is not None
            assert sync_process.stderr is not None

            # Send handshake (shared preparation with async version)
            handshake_bytes = self._prepare_handshake(self._colors)
            sync_process.stdin.write(handshake_bytes)
            sync_process.stdin.flush()

            # Read and validate handshake response (shared parsing with async version)
            handshake_response = sync_process.stdout.readline()
            self._parse_handshake_response(handshake_response)

            # Send command
            sync_process.stdin.write(json_bytes)
            sync_process.stdin.flush()

            # Process messages until done (continues reading until EOF after terminal message)
            while True:
                line = sync_process.stdout.readline()
                if not line:
                    break
                self._handle_message(line)

            # Wait for process to finish (with timeout)
            timeout_sec = params.processExitTimeout if params and params.processExitTimeout is not None else 3.0
            try:
                sync_process.wait(timeout=timeout_sec)
            except subprocess.TimeoutExpired:
                sync_process.kill()
                sync_process.wait()

            # Read stderr at end and track it
            # Note: Using stderr=sys.stderr would be simpler but errors would go unnoticed
            stderr_bytes = sync_process.stderr.read()
            if stderr_bytes:
                stderr_text = stderr_bytes.decode('utf-8', errors='replace')
                sys.stderr.write(stderr_text)
                sys.stderr.flush()
                self._stderr_output = stderr_text.strip().splitlines()

            # Check if stderr had output (indicates solver crash/error)
            if self._stderr_output:
                stderr_text = '\n'.join(self._stderr_output)
                raise RuntimeError(f"Solver error:\n{stderr_text}")

            # Check for errors from solver messages
            if self._errors:
                error_summary = '\n'.join(self._errors)
                raise RuntimeError(f"Solver reported error(s):\n{error_summary}")

            # Check if we got expected result (after reading stderr for better error message)
            if not self._raw_summary_data and not self._text_result and not self._errors and not self._stderr_output:
                raise RuntimeError("Solver closed unexpectedly without sending results")

            return_code = sync_process.returncode
            if return_code != 0:
                raise RuntimeError(
                    f"Solver failed with return code {return_code}."
                )

        except Exception:
            if sync_process is not None and sync_process.returncode is None:
                sync_process.kill()
                sync_process.wait()
            raise

        finally:
            signal.signal(signal.SIGINT, original_sigint_handler)

    def _sync_solve(self,
                    model: Model,
                    params: Parameters | None = None,
                    warm_start: Solution | None = None) -> SolveResult:
        """
        Solve the model synchronously.

        This is the internal method called by Model.solve().

        Args:
            model: The model to solve
            params: Optional solver parameters
            warm_start: Optional initial solution

        Returns:
            SolveResult with solution and statistics
        """
        self._sync_run("solve", model, params, warm_start)

        if self._raw_summary_data is None:
            raise RuntimeError("Solver did not return a summary message")

        return SolveResult(
            self._raw_summary_data,
            self._solution,
            self._solutions,
            self._objective_history,
            self._lower_bound_history,
            self._solution_time,
            self._best_lb_time,
            self._solution_valid
        )

    def _sync_to_text(self,
                      model: Model,
                      params: Parameters | None = None,
                      warm_start: Solution | None = None) -> str:
        """
        Convert model to text format synchronously.

        This is the internal method called by Model.to_txt().

        Args:
            model: The model to convert
            params: Optional solver parameters
            warm_start: Optional initial solution

        Returns:
            Text representation of the model
        """
        self._sync_run("toText", model, params, warm_start)

        if self._text_result is None:
            raise RuntimeError("Solver did not return a textModel message")

        return self._text_result

    def _sync_to_js(self,
                    model: Model,
                    params: Parameters | None = None,
                    warm_start: Solution | None = None) -> str:
        """
        Convert model to JavaScript format synchronously.

        This is the internal method called by Model.to_js().

        Args:
            model: The model to convert
            params: Optional solver parameters
            warm_start: Optional initial solution

        Returns:
            JavaScript representation of the model
        """
        self._sync_run("toJS", model, params, warm_start)

        if self._text_result is None:
            raise RuntimeError("Solver did not return a textModel message")

        return self._text_result
