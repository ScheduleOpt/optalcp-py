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
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import IO, Any, final

from . import __version__  # Import version for handshake
from ._model import Model
from ._parameters import Parameters
from ._result import (
    ObjectiveBoundEntry,
    ObjectiveEntry,
    SolveResult,
    SolveSummary,
    _RawSolveSummary,
)
from ._serialization import _serialize_to_json
from ._solution import Solution
from ._utils import _can_use_colors, _find_solver_path

# === Event Types ============================================================

@final
@dataclass(frozen=True, slots=True)
class SolutionEvent:
    r"""
    An event emitted when a solution is found.

    This event is passed to the :attr:`Solver.on_solution` callback and contains
    the solution, solving time so far, and the result of solution verification.

    .. code-block:: python

        import optalcp as cp

        model = cp.Model()
        x = model.interval_var(length=10, name="x")
        model.minimize(x.end())

        async def handle_solution(event: cp.SolutionEvent):
            print(f"Solution found at {event.solve_time:.2f}s")
            print(f"Objective: {event.solution.get_objective()}")
            if event.valid is not None:
                print(f"Verified: {event.valid}")

        solver = cp.Solver(on_solution=handle_solution)
        result = await solver.solve(model)

    .. seealso::

        - :class:`Solver` for the Python solver API.
        - :attr:`Solver.on_solution` to register a solution callback.
    """

    solve_time: float
    r"""
    The duration of the solve at the time the solution was found, in seconds.
    """

    solution: Solution
    r"""
    The solution containing values for all variables and the objective value.

    The solution contains values of all variables in the model (including
    optional variables) and the value of the objective (if the model specified
    one).

    .. seealso::

        - :class:`Solution` for accessing variable values.
    """

    valid: bool | None = None
    r"""
    Result of the verification of the solution.

    When parameter :attr:`Parameters.verifySolutions` is set to `True` (the
    default), the solver verifies all solutions found. The
    verification checks that all constraints in the model are satisfied and
    that the objective value is computed correctly.

    The verification is done using a separate code (not used during the
    search). The point is to independently verify the correctness of the
    solution.

    Possible values are:

    * `None` - the solution was not verified (because the parameter
      :attr:`Parameters.verifySolutions` was not set).
    * `True` - the solution was verified and correct.

    The value can never be `False` because, in that case, the solver ends with an
    error.
    """


class Solver:
    r"""
    Provides asynchronous communication with the solver subprocess.

    Unlike function :meth:`Model.solve`, `Solver` allows the user to process individual events
    during the solve and to stop the solver at any time. If you're
    interested in the final result only, use :meth:`Model.solve` instead.

    To solve a model, create a new `Solver` object and call its method :meth:`Solver.solve`.

    The Python Solver uses callback properties to handle events:

    * :attr:`Solver.on_error`: Called with a `str` message when an error occurs.
    * :attr:`Solver.on_warning`: Called with a `str` for every issued warning.
    * :attr:`Solver.on_log`: Called with a `str` for every log message.
    * :attr:`Solver.on_solution`: Called with a :class:`SolutionEvent` when a solution is found.
    * :attr:`Solver.on_objective_bound`: Called with an `ObjectiveBoundEntry` when a new bound is proved.
    * :attr:`Solver.on_summary`: Called with a :class:`SolveSummary` at the end of the solve.

    The solver output (log, trace, and warnings) is printed to :attr:`Solver.output_stream` by default
    (which defaults to `sys.stdout`). It can be redirected to a file or suppressed by setting
    `output_stream` to `None`.

    ## Example

    In the following example, we run a solver asynchronously. We set up an
    `on_solution` callback to print the objective value of the solution
    and the value of interval variable `x`. After finding the first solution, we request
    the solver to stop.
    We also set up an `on_summary` callback to print statistics about the solve.

    .. code-block:: python

        import optalcp as cp

        model = cp.Model()
        x = model.interval_var(length=10, name="x")
        model.minimize(x.end())

        # Create a new solver:
        solver = cp.Solver()

        # Define solution handler:
        async def handle_solution(event: cp.SolutionEvent):
            solution = event.solution
            print(f"At time {event.solve_time:.2f}, solution found with objective {solution.get_objective()}")
            # Print value of interval variable x:
            if solution.is_absent(x):
                print("  Interval variable x is absent")
            else:
                print(f"  Interval variable x: [{solution.get_start(x)} -- {solution.get_end(x)}]")
            # Request the solver to stop as soon as possible:
            await solver.stop("We are happy with the first solution found.")

        # Define summary handler:
        def handle_summary(summary: cp.SolveSummary):
            print(f"Total duration of solve: {summary.duration}")
            print(f"Number of branches: {summary.nb_branches}")

        # Set callbacks:
        solver.on_solution = handle_solution
        solver.on_summary = handle_summary

        # Solve (async):
        result = await solver.solve(model, cp.Parameters(time_limit=60))
        print("All done")
    """

    @property
    def output_stream(self) -> IO[str] | None:
        r"""
        The stream where log and warning messages are written.

        Can be set to any file-like object (file, `sys.stdout`, `sys.stderr`, etc.) or `None` to disable automatic output. When set to `None`, messages are not printed but callbacks (:attr:`Solver.on_log`, :attr:`Solver.on_warning`) still receive them.

        This is different from setting :attr:`Parameters.logLevel` to 0, which disables log message generation entirely.

        The default value is `sys.stdout`.

        .. code-block:: python

            solver = cp.Solver()

            # Redirect to stderr
            solver.output_stream = sys.stderr

            # Disable automatic printing (callbacks still receive messages)
            solver.output_stream = None

            # Write to a file
            with open("solver.log", "w") as f:
                solver.output_stream = f
                result = await solver.solve(model)

        .. seealso::

            - :attr:`Solver.on_log` for custom log message handling.
            - :attr:`Solver.on_warning` for custom warning message handling.
            - :attr:`Parameters.logLevel` to control log message generation.
        """
        return self._output_stream

    @output_stream.setter
    def output_stream(self, value: IO[str] | None) -> None:
        self._output_stream = value

    @property
    def on_log(self) -> Callable[[str], None] | Callable[[str], Awaitable[None]] | None:
        r"""
        Callback invoked for each log message.

        The callback is called for each log message, after the message is written to :attr:`Solver.output_stream`. The default is `None` (no custom callback).

        The callback receives one argument:

        - `msg` (`str`): The log message text.

        The callback can be either synchronous or asynchronous.

        .. code-block:: python

            solver = cp.Solver()

            # Synchronous callback
            solver.on_log = lambda msg: my_logger.info(msg)

            # Or with a named function
            def log_handler(msg: str) -> None:
                print(f"LOG: {msg}")

            solver.on_log = log_handler

            # Asynchronous callback
            async def async_log_handler(msg: str) -> None:
                await async_logger.info(msg)

            solver.on_log = async_log_handler

        The amount of log messages and their periodicity can be controlled by :attr:`Parameters.logLevel` and :attr:`Parameters.logPeriod`.

        .. seealso::

            - :attr:`Solver.output_stream` for redirecting output to a stream.
            - :attr:`Solver.on_warning` for warning messages.
        """
        return self._on_log

    @on_log.setter
    def on_log(self, value: Callable[[str], None] | Callable[[str], Awaitable[None]] | None) -> None:
        self._on_log = value

    @property
    def on_warning(self) -> Callable[[str], None] | Callable[[str], Awaitable[None]] | None:
        r"""
        Callback function for warning messages from the solver.

        The callback is called for each warning message, after the message is written to :attr:`Solver.output_stream`. The default is `None` (no custom callback).

        The callback receives one argument:

        - `msg` (`str`): The warning message text.

        The callback can be either synchronous or asynchronous.

        .. code-block:: python

            solver = cp.Solver()

            # Synchronous callback
            solver.on_warning = lambda msg: warnings.warn(msg)

            # Asynchronous callback
            async def async_warning_handler(msg: str) -> None:
                await async_logger.warning(msg)

            solver.on_warning = async_warning_handler

        The amount of warning messages can be configured using :attr:`Parameters.warningLevel`.

        .. seealso::

            - :attr:`Solver.output_stream` for redirecting output to a stream.
            - :attr:`Solver.on_log` for log messages.
            - :attr:`Solver.on_error` for error messages.
        """
        return self._on_warning

    @on_warning.setter
    def on_warning(self, value: Callable[[str], None] | Callable[[str], Awaitable[None]] | None) -> None:
        self._on_warning = value

    @property
    def on_error(self) -> Callable[[str], None] | Callable[[str], Awaitable[None]] | None:
        r"""
        Callback function for error messages from the solver.

        The callback is called for each error message. Errors are also written to `sys.stderr`. The default is `None` (no custom callback).

        The callback receives one argument:

        - `msg` (`str`): The error message text.

        The callback can be either synchronous or asynchronous.

        .. code-block:: python

            solver = cp.Solver()

            # Synchronous callback
            solver.on_error = lambda msg: print(f"ERROR: {msg}", file=sys.stderr)

            # Asynchronous callback
            async def async_error_handler(msg: str) -> None:
                await async_logger.error(msg)

            solver.on_error = async_error_handler

        An error message indicates that the solve is closing. However, other messages (log, warning, solution) may still arrive after the error.

        Error messages are accumulated during solving and raised as `RuntimeError` at the end of the solve.

        .. seealso::

            - :attr:`Solver.on_warning` for warning messages.
            - :attr:`Solver.on_log` for log messages.
        """
        return self._on_error

    @on_error.setter
    def on_error(self, value: Callable[[str], None] | Callable[[str], Awaitable[None]] | None) -> None:
        self._on_error = value

    @property
    def on_solution(self) -> Callable[[SolutionEvent], None] | Callable[[SolutionEvent], Awaitable[None]] | None:
        r"""
        Callback function for solution events from the solver.

        The callback is called each time the solver finds a new solution. The default is `None` (no custom callback).

        The callback receives one argument:

        - `event` (:class:`SolutionEvent`): A dataclass with the following fields:
           - `solution` (:class:`Solution`): The solution object with variable values.
           - `solve_time` (`float`): Time when the solution was found (seconds since solve start).
           - `valid` (`bool | None`): Solution verification result if enabled, `None` otherwise.

        The callback can be either synchronous or asynchronous.

        .. code-block:: python

            def handle_solution(event: cp.SolutionEvent) -> None:
                sol = event.solution
                time = event.solve_time
                print(f"Solution found at {time:.2f}s, objective={sol.get_objective()}")

            solver = cp.Solver()
            solver.on_solution = handle_solution

            # Asynchronous callback
            async def async_handle_solution(event: cp.SolutionEvent) -> None:
                sol = event.solution
                await save_to_database(sol)

            solver.on_solution = async_handle_solution

        .. seealso::

            - :class:`SolutionEvent` for the event structure.
            - :class:`Solution` for accessing variable values.
            - :attr:`Solver.on_objective_bound` for objective bound updates.
        """
        return self._on_solution

    @on_solution.setter
    def on_solution(self, value: Callable[[SolutionEvent], None] | Callable[[SolutionEvent], Awaitable[None]] | None) -> None:
        self._on_solution = value

    @property
    def on_objective_bound(self) -> Callable[[ObjectiveBoundEntry], None] | Callable[[ObjectiveBoundEntry], Awaitable[None]] | None:
        r"""
        Callback function for objective bound events from the solver.

        The callback is called when the solver improves the bound on the objective (lower bound for minimization, upper bound for maximization). The default is `None` (no custom callback).

        The callback receives one argument:

        - `event` (:class:`ObjectiveBoundEntry`): A dataclass with the following fields:
           - `value` (`float`): The new bound value.
           - `solve_time` (`float`): Time when the bound was proved (seconds since solve start).

        The callback can be either synchronous or asynchronous.

        .. code-block:: python

            solver = cp.Solver()

            # Synchronous callback
            solver.on_objective_bound = lambda event: print(f"Bound: {event.value}")

            # Asynchronous callback
            async def async_bound_handler(event: cp.ObjectiveBoundEntry) -> None:
                await update_dashboard(event.value)

            solver.on_objective_bound = async_bound_handler

        .. seealso::

            - :class:`ObjectiveBoundEntry` for the event structure.
            - :attr:`Solver.on_solution` for solution events with objective values.
        """
        return self._on_objective_bound

    @on_objective_bound.setter
    def on_objective_bound(self, value: Callable[[ObjectiveBoundEntry], None] | Callable[[ObjectiveBoundEntry], Awaitable[None]] | None) -> None:
        self._on_objective_bound = value

    @property
    def on_summary(self) -> Callable[[SolveSummary], None] | Callable[[SolveSummary], Awaitable[None]] | None:
        r"""
        Callback function for solve completion event.

        The callback is called once when the solve completes, providing final statistics. The default is `None` (no custom callback).

        The callback receives one argument:

        - `summary` (:class:`SolveSummary`): Solve statistics with properties including:
           - `nb_solutions` (`int`): Number of solutions found.
           - `duration` (`float`): Total solve time in seconds.
           - `nb_branches` (`int`): Number of branches explored.
           - `objective` (`float | None`): Best objective value, or `None` if no solution found.
           - Plus many other statistics (see :class:`SolveSummary`).

        The callback can be either synchronous or asynchronous.

        .. code-block:: python

            def handle_summary(summary: cp.SolveSummary) -> None:
                print(f"Solve completed: {summary.nb_solutions} solutions")
                print(f"Time: {summary.duration:.2f}s")
                if summary.objective is not None:
                    print(f"Best objective: {summary.objective}")

            solver = cp.Solver()
            solver.on_summary = handle_summary

            # Asynchronous callback
            async def async_handle_summary(summary: cp.SolveSummary) -> None:
                await save_stats_to_db(summary)

            solver.on_summary = async_handle_summary

        .. seealso::

            - :class:`SolveSummary` for the complete list of statistics.
        """
        return self._on_summary

    @on_summary.setter
    def on_summary(self, value: Callable[[SolveSummary], None] | Callable[[SolveSummary], Awaitable[None]] | None) -> None:
        self._on_summary = value

    def __init__(self) -> None:
        r"""
        Creates a solver instance for asynchronous solving.

        Callbacks and output stream can be configured after instantiation using the
        properties: :attr:`Solver.output_stream`, :attr:`Solver.on_log`,
        :attr:`Solver.on_warning`, :attr:`Solver.on_error`, :attr:`Solver.on_solution`,
        :attr:`Solver.on_objective_bound`, :attr:`Solver.on_summary`.

        .. code-block:: python

            solver = cp.Solver()
            solver.output_stream = None  # Disable output
            solver.on_solution = lambda event: print("Found solution!")
            result = await solver.solve(model)

        .. seealso::

            - :meth:`Solver.solve` to solve a model asynchronously.
            - :meth:`Model.solve` for simpler synchronous solving.
        """
        # Initialize output stream and callbacks to default values
        self._output_stream = sys.stdout
        self._on_log = None
        self._on_warning = None
        self._on_error = None
        self._on_solution = None
        self._on_objective_bound = None
        self._on_summary = None

        self._process: asyncio.subprocess.Process | None = None
        self._stop_requested = False
        self._colors = False
        self._solver_path = ""
        self._solution: Solution | None = None
        self._objective_history: list[ObjectiveEntry] = []
        self._objective_bound_history: list[ObjectiveBoundEntry] = []
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
        - _solution, etc.: For solution tracking

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
            except TimeoutError:
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
        Solves a model with the specified parameters.

        :param model: The model to solve
        :type model: Model
        :param params: The parameters for the solver
        :type params: Parameters | None
        :param warm_start: An initial solution to start the solver with
        :type warm_start: Solution | None
        :rtype: SolveResult
        :returns: The result of the solve when finished.

        ## Details

        The solving process runs asynchronously. Use `await` to wait for the
        solver to finish.  During the solve, the solver emits events that can be
        intercepted using callback properties like :attr:`Solver.on_solution`,
        :attr:`Solver.on_log`, etc.

        Communication with the solver subprocess happens through the event loop.
        The user code must yield control (using `await` or waiting for an event)
        for the solver to receive commands and send updates.

        ### Warm start and external solutions

        If the `warm_start` parameter is specified, the solver will start with the
        given solution.  The solution must be compatible with the model; otherwise
        an error is raised.  The solver will take advantage of the
        solution to speed up the search: it will search only for better solutions
        (if it is a minimization or maximization problem). The solver may try to
        improve the provided solution by Large Neighborhood Search.

        There are two ways to pass a solution to the solver: using `warm_start`
        parameter and using function :meth:`Solver.send_solution`.
        The difference is that `warm_start` is guaranteed to be used by the solver
        before the solve starts.  On the other hand, `send_solution` can be called
        at any time during the solve.

        Parameter :attr:`Parameters.lnsUseWarmStartOnly` controls whether the
        solver should only use the warm start solution (and not search for other
        initial solutions). If no warm start is provided, the solver searches for
        its own initial solution as usual.
        """
        await self._run("solve", model, params, warm_start)

        if self._raw_summary_data is None:
            raise RuntimeError("Solver did not return a summary message")

        # Build and return SolveResult from stored data
        return SolveResult(
            self._raw_summary_data,
            self._solution,
            self._objective_history,
            self._objective_bound_history,
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
        Requests the solver to stop as soon as possible.

        :param reason: The reason why to stop. The reason will appear in the log
        :type reason: str

        ## Details

        This method only initiates the stop; it returns immediately without waiting
        for the solver to actually stop. The solver will stop as soon as possible and
        will send a summary event. However, other events may be sent
        before the summary event (e.g., another solution found or a log message).

        Requesting a stop on a solver that has already stopped has no effect.

        ## Example

        In the following example, we issue a stop command 1 minute after the first
        solution is found.

        .. code-block:: python

            import optalcp as cp
            import threading

            solver = cp.Solver()
            timer_started = False

            def on_solution(event):
                global timer_started
                # We just found a solution. Set a timeout if there isn't any.
                if not timer_started:
                    timer_started = True
                    # Register a function to be called after 60 seconds:
                    def stop_solver():
                        print("Requesting solver to stop")
                        solver.stop("Stop because I said so!")
                    timer = threading.Timer(60.0, stop_solver)  # The timeout is 60 seconds
                    timer.start()

            solver.on_solution = on_solution
            result = await solver.solve(model, cp.Parameters(timeLimit=300))
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

        ## Details

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
        :attr:`Parameters.logLevel` is set to 0, the solver will log a message when it
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

        message_bytes = _serialize_to_json(message) + b'\n'
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
        :type params: Parameters | None
        :param warm_start: Optional initial solution to include
        :type warm_start: Solution | None
        :rtype: str
        :returns: A string containing the model in JSON format.

        ## Details

        Async version of :meth:`Model.to_json`.

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

            - :meth:`Model.to_json` for synchronous usage.
            - :meth:`Model.from_json` to import from JSON.
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
        :type params: Parameters | None
        :param warm_start: Optional initial solution to include
        :type warm_start: Solution | None
        :rtype: str
        :returns: Text representation of the model.

        ## Details

        Async version of :meth:`Model.to_txt`. This method communicates with
        the solver process to generate the text output.

        The output is human-readable and similar to the IBM CP Optimizer file format.

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

            - :meth:`Model.to_txt` for synchronous usage.
            - :meth:`Solver.to_js` for JavaScript export.
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
        :type params: Parameters | None
        :param warm_start: Optional initial solution to include
        :type warm_start: Solution | None
        :rtype: str
        :returns: JavaScript code representing the model.

        ## Details

        Async version of :meth:`Model.to_js`. This method communicates with
        the solver process to generate the JavaScript output.

        The output is human-readable, executable with Node.js, and can be stored
        in a file.

        This feature is experimental and the result is not guaranteed to be valid
        in all cases.

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

            - :meth:`Model.to_js` for synchronous usage.
            - :meth:`Solver.to_txt` for text format export.
        """
        return await self._to_text("toJS", model, params, warm_start)

    # =========================================================================
    # Shared helper methods (used by both sync and async solving)
    # =========================================================================

    def _reset_state(self) -> None:
        """Reset solver state before a new solve/conversion operation."""
        self._stop_requested = False
        self._solution = None
        self._objective_history = []
        self._objective_bound_history = []
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

        json_bytes = _serialize_to_json(model_data)

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
            raise RuntimeError(f"Invalid handshake response: {e}") from e

    def _prepare_handshake(self, colors: bool) -> bytes:
        """Prepare handshake message bytes to send to solver."""
        handshake: dict[str, Any] = {
            "msg": "handshake", "version": __version__, "colors": colors}
        return _serialize_to_json(handshake) + b'\n'

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
            raise RuntimeError(f"Invalid JSON from solver: {e}") from e

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

            history_item = ObjectiveEntry(
                solve_time=data['solveTime'],
                objective=solution.get_objective(),
                valid=data.get('verifiedOK')
            )
            self._objective_history.append(history_item)

            self._solution_time = data['solveTime']
            if 'verifiedOK' in data:
                self._solution_valid = data['verifiedOK']

            event = SolutionEvent(
                solve_time=data['solveTime'],
                solution=solution,
                valid=data.get('verifiedOK')
            )
            self._call_handler(self.on_solution, event)
            return True

        if msg_type == 'lowerBound' and data is not None:
            bound_event = ObjectiveBoundEntry(
                solve_time=data['solveTime'],
                value=data['value']
            )
            self._objective_bound_history.append(bound_event)
            self._best_lb_time = data['solveTime']
            self._call_handler(self.on_objective_bound, bound_event)
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
                        stop_bytes = _serialize_to_json(stop_msg) + b'\n'
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
            self._objective_history,
            self._objective_bound_history,
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
