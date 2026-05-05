"""
Benchmark API.

Spawns the ``optalcp benchmark`` coordinator subprocess and feeds it a
stream of models from a user-supplied iterable. Results (progress table,
per-seed output files) land in a run directory on disk; the function
returns nothing.

This is v1: no viewer integration, no model-name enforcement, no
per-worker parameters at the benchmark level. See
``docs/DESIGN-v2.md`` in the viewer repo for the full design.
"""

from __future__ import annotations

import contextlib
import json
import signal
import subprocess
import sys
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, NoReturn, cast

from ._model import Model
from ._parameters import (
    _PYTHON_SPECIFIC_FIELDS,
    Parameters,
    _handle_help_flags,
    _ParameterParser,
    _parameters_to_json,
    _parse_bool,
    _parse_int,
    copy_parameters,
)
from ._serialization import _serialize_to_json
from ._solution import Solution

# === SolveInput =============================================================

@dataclass
class SolveInput:
    """A model bundled with optional per-instance parameters and warm start.

    Used as an item of the iterable passed to :func:`benchmark`. A bare
    :class:`Model` is accepted instead; it is wrapped internally.
    """

    model: Model
    parameters: Parameters | None = None
    warm_start: Solution | None = None


# === BenchmarkParameters ===================================================

class BenchmarkParameters(Parameters, total=False):
    """Parameters for :func:`benchmark`.

    Extends :class:`Parameters` with benchmark-specific keys. Engine
    parameters (``timeLimit``, ``nbWorkers``, ``searchType``, etc.) can
    be specified at the benchmark level as defaults; per-instance
    parameters in :class:`SolveInput` override them.
    """

    nbSeeds: int
    nbParallelRuns: int
    outputDir: str
    name: str
    solve: bool
    exportSolution: bool
    exportText: bool
    exportJS: bool


# === CLI argument handling =================================================

# Flag name (lowercased, no leading --) → (canonical key, type parser).
# Used to recognize benchmark-specific flags before handing the rest off
# to the engine parameter parser.
_BENCHMARK_FLAG_SPECS: dict[str, tuple[str, Any]] = {
    'nbseeds':        ('nbSeeds',        _parse_int),
    'nbparallelruns': ('nbParallelRuns', _parse_int),
    'outputdir':      ('outputDir',      lambda v, n: v),
    'name':           ('name',           lambda v, n: v),
    'solve':          ('solve',          _parse_bool),
    'exportsolution': ('exportSolution', _parse_bool),
    'exporttext':     ('exportText',     _parse_bool),
    'exportjs':       ('exportJS',       _parse_bool),
}


_BENCHMARK_PARAMETERS_HELP = """\

Benchmark parameters:
  --nbSeeds N            Run each model N times with different random seeds (default: 1).
  --nbParallelRuns N     Execute up to N solver subprocesses concurrently (default: 1).
  --outputDir PATH       Root directory for benchmark outputs (default: temp directory).
  --name NAME            Display name for the benchmark run.
  --solve BOOL           Run the solve (default: true). False skips solving.
  --exportSolution BOOL  Write solution.json per seed (default: true).
  --exportText BOOL      Write input.txt per instance in text format (default: false).
  --exportJS BOOL        Write input.js per instance in executable JavaScript (default: false).
"""


def _extract_benchmark_args(
    args: list[str],
) -> tuple[dict[str, Any], list[str]]:
    """Consume benchmark-specific flags from ``args``.

    Returns the collected key/value dict and the list of remaining
    arguments (to be fed to the engine parameter parser).
    """
    out: dict[str, Any] = {}
    remaining: list[str] = []
    i = 0
    while i < len(args):
        tok = args[i]
        if not tok.startswith('--'):
            remaining.append(tok)
            i += 1
            continue

        # Support --key=value and --key value.
        eq_pos = tok.find('=')
        if eq_pos != -1:
            flag = tok[2:eq_pos].lower()
            value: str | None = tok[eq_pos + 1:]
        else:
            flag = tok[2:].lower()
            value = None

        spec = _BENCHMARK_FLAG_SPECS.get(flag)
        if spec is None:
            remaining.append(tok)
            i += 1
            continue

        canonical, parser = spec
        if value is None:
            if i == len(args) - 1:
                raise ValueError(f"Missing value for command line option: {tok}")
            value = args[i + 1]
            i += 2
        else:
            i += 1

        out[canonical] = parser(value, canonical)

    return out, remaining


def parse_benchmark_parameters(
    *,
    args: list[str] | None = None,
    defaults: BenchmarkParameters | None = None,
    usage: str | None = None,
    exit_on_error: bool = True,
) -> BenchmarkParameters:
    """Parse benchmark-level parameters from the command line (strict).

    Accepts both benchmark-specific flags (``--nbSeeds``, ``--outputDir``,
    etc.) and engine parameters (``--timeLimit``, ``--nbWorkers``, ...).
    Any unrecognized argument is an error.

    :param args: Command-line arguments to parse. Defaults to ``sys.argv[1:]``.
    :type args: list[str] | None
    :param defaults: Default values. CLI arguments override these.
    :type defaults: BenchmarkParameters | None
    :param usage: Usage string printed before help output.
    :type usage: str | None
    :param exit_on_error: If ``True`` (default), print errors and ``--help``
        output then exit. If ``False``, raise ``ValueError`` instead.
    :type exit_on_error: bool
    :rtype: BenchmarkParameters
    :returns: The parsed :class:`BenchmarkParameters` dict.
    """
    params, _ = _parse_impl(
        args=args,
        defaults=defaults,
        usage=usage,
        exit_on_error=exit_on_error,
        allow_unknown=False,
    )
    return params


def parse_known_benchmark_parameters(
    *,
    args: list[str] | None = None,
    defaults: BenchmarkParameters | None = None,
    usage: str | None = None,
    exit_on_error: bool = True,
) -> tuple[BenchmarkParameters, list[str]]:
    """Parse benchmark-level parameters, passing through unrecognized arguments.

    Same as :func:`parse_benchmark_parameters` but returns unrecognized
    arguments as the second tuple element instead of erroring on them.
    This is the form used by the jobshop-style pattern where positional
    model-file arguments are mixed with flags.

    :param args: Command-line arguments to parse. Defaults to ``sys.argv[1:]``.
    :type args: list[str] | None
    :param defaults: Default values. CLI arguments override these.
    :type defaults: BenchmarkParameters | None
    :param usage: Usage string printed before help output.
    :type usage: str | None
    :param exit_on_error: If ``True`` (default), print errors and ``--help``
        output then exit. If ``False``, raise ``ValueError`` instead.
    :type exit_on_error: bool
    :rtype: tuple[BenchmarkParameters, list[str]]
    :returns: The parsed :class:`BenchmarkParameters` dict and the list of
        unrecognized command-line arguments.
    """
    return _parse_impl(
        args=args,
        defaults=defaults,
        usage=usage,
        exit_on_error=exit_on_error,
        allow_unknown=True,
    )


def _parse_impl(
    *,
    args: list[str] | None,
    defaults: BenchmarkParameters | None,
    usage: str | None,
    exit_on_error: bool,
    allow_unknown: bool,
) -> tuple[BenchmarkParameters, list[str]]:
    if args is None:
        args = sys.argv[1:]

    params: BenchmarkParameters = (
        cast(BenchmarkParameters, copy_parameters(defaults))
        if defaults
        else cast(BenchmarkParameters, {})
    )

    _handle_help_flags(args, usage, exit_on_error, extra_help=_BENCHMARK_PARAMETERS_HELP)

    def _run() -> list[str]:
        bench_kv, remainder = _extract_benchmark_args(args)
        engine_parser = _ParameterParser(cast(Parameters, params))
        if allow_unknown:
            engine_parser.allow_unknown()
        engine_parser.parse(remainder)
        for key, value in bench_kv.items():
            params[key] = value  # type: ignore[literal-required]
        return engine_parser.get_unrecognized()

    if exit_on_error:
        try:
            unknown = _run()
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        unknown = _run()

    return params, unknown


# === CLI arg emission (Python → binary) ====================================

# Parameter keys that are intentionally not forwarded to the binary:
# - _PYTHON_SPECIFIC_FIELDS (printLog, solver, solverArgs, ...) are
#   handled on the Python side.
_CLI_EXCLUDED_FIELDS = _PYTHON_SPECIFIC_FIELDS


def _params_to_cli_args(params: BenchmarkParameters) -> list[str]:
    """Flatten ``BenchmarkParameters`` into ``--key=value`` tokens for the binary.

    The ``--key=value`` form (rather than two separate tokens) prevents
    a value that starts with ``-`` from being mis-parsed as another
    flag by the binary's CLI parser.

    For v1, only flat keys are supported. A ``workers`` list raises
    ``ValueError`` — use per-instance :class:`SolveInput` ``parameters``
    for worker-level configuration instead.
    """
    def format_value(v: object) -> str:
        if isinstance(v, bool):
            return 'true' if v else 'false'
        if v == float('inf'):
            return 'Infinity'
        if v == float('-inf'):
            return '-Infinity'
        return str(v)

    out: list[str] = []
    for key, value in params.items():
        if key in _CLI_EXCLUDED_FIELDS:
            continue
        if value is None:
            continue
        if key == 'workers':
            raise ValueError(
                "Per-worker parameters at the benchmark level are not "
                "supported in v1. Specify worker parameters on the "
                "per-instance SolveInput.parameters instead."
            )
        # Hidden/internal parameters are stored with a leading '_' in the
        # dict (e.g. '_lnsAlternativeWeight'). The solver's CLI parser
        # recognizes the bare name, so strip the marker when emitting.
        cli_key = key[1:] if key.startswith('_') else key
        out.append(f'--{cli_key}={format_value(value)}')
    return out


# === benchmark() ============================================================

_EMPTY_INPUT_MESSAGE = (
    "No input models were provided to benchmark. "
    "At least one model is required."
)

# How long (seconds) to wait for the stdin-writer thread to finish after the
# subprocess has closed stdout. The writer is normally done well before this;
# the timeout guards against a pathologically slow model serialization so
# benchmark() cannot hang forever.
_WRITER_JOIN_TIMEOUT = 5.0

# How long (seconds) to wait for the subprocess to exit after stdout closed.
# The subprocess has already finished producing output by this point; this
# just guards against it hanging during cleanup. On timeout we escalate to
# kill() and wait() again — unconditional this time.
_PROC_WAIT_TIMEOUT = 5.0


def _fail(message: str, exit_on_error: bool, exc_type: type[Exception]) -> NoReturn:
    """Emit an error: print-and-exit or raise, per ``exit_on_error``."""
    if exit_on_error:
        print(f"Error: {message}", file=sys.stderr)
        sys.exit(1)
    raise exc_type(message)


def _model_json_line(item: Model | SolveInput) -> bytes:
    """Serialize a single benchmark input to its stdin line.

    The format matches what ``master/benchmark.cpp:ingestModelFromJson``
    expects: the model dict optionally augmented with ``parameters`` and
    ``warmStart`` keys.
    """
    if isinstance(item, Model):
        model, parameters, warm_start = item, None, None
    else:
        model, parameters, warm_start = item.model, item.parameters, item.warm_start

    data: dict[str, Any] = model._to_dict()
    if parameters:
        data['parameters'] = _parameters_to_json(parameters)
    if warm_start is not None:
        data['warmStart'] = warm_start._to_dict()

    return _serialize_to_json(data) + b'\n'


def benchmark(
    inputs: Iterable[Model | SolveInput],
    params: BenchmarkParameters | None = None,
    *,
    exit_on_error: bool = True,
) -> None:
    """Run a benchmark over an iterable of models.

    Each item is pulled, serialized, and fed to the ``optalcp benchmark``
    coordinator subprocess. Memory usage stays bounded by one model
    because the iterator is consumed lazily. Results (progress table on
    stdout, run directory on disk) are produced as side effects.

    :param inputs: An iterable yielding :class:`Model` or :class:`SolveInput`
        items. At least one item is required.
    :type inputs: Iterable[Model | SolveInput]
    :param params: Benchmark-level parameters. Per-instance parameters
        on ``SolveInput`` override these.
    :type params: BenchmarkParameters | None
    :param exit_on_error: If ``True`` (default), startup errors print a
        one-line message to stderr and exit the process with status 1.
        If ``False``, errors raise ``ValueError`` (empty input) or
        ``RuntimeError`` (subprocess failures) instead.
    :type exit_on_error: bool
    """
    if params is None:
        params = cast(BenchmarkParameters, {})

    # Eagerly pull the first item to detect an empty iterable before we
    # spawn anything. StopIteration becomes a clean error.
    iterator = iter(inputs)
    try:
        first_item: Model | SolveInput = next(iterator)
    except StopIteration:
        _fail(_EMPTY_INPUT_MESSAGE, exit_on_error, ValueError)

    # Locate the solver binary. find_solver raises FileNotFoundError on
    # misconfiguration — surface it per exit_on_error.
    from ._solver import Solver  # local import to avoid circular dependency
    try:
        solver_path = Solver.find_solver(params)
    except FileNotFoundError as e:
        _fail(str(e), exit_on_error, RuntimeError)

    argv = [solver_path, 'benchmark', '--api=1', *_params_to_cli_args(params)]

    # stderr is not captured: the binary routes real errors into per-seed
    # log.txt and the {"msg":"error"} protocol. Leaving stderr on the
    # user's terminal avoids a pipe-buffer deadlock if the binary writes
    # more than the ~64KB kernel buffer before exiting.
    proc = subprocess.Popen(
        argv,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
    )
    assert proc.stdin is not None
    assert proc.stdout is not None

    # Hand the first item off to the writer thread through a single-slot
    # list, then clear the outer reference so the main thread's frame
    # does not pin the model in memory for the benchmark's duration.
    # DO NOT REMOVE: bounds peak memory to one model (see design doc,
    # "Memory property" in the benchmark API surface section).
    first_slot: list[Model | SolveInput | None] = [first_item]
    del first_item

    # Shared state between threads.
    writer_error: list[Exception] = []
    seen_error_from_solver: list[str] = []

    def stdin_writer() -> None:
        try:
            item: Model | SolveInput | None = first_slot[0]
            first_slot[0] = None
            while item is not None:
                line = _model_json_line(item)
                proc.stdin.write(line)  # type: ignore[union-attr]
                proc.stdin.flush()  # type: ignore[union-attr]
                # Release the current model before pulling the next so peak
                # memory stays bounded by one model.
                del item, line
                item = next(iterator, None)
        except BrokenPipeError:
            # Subprocess closed stdin (likely dying); error will surface
            # via stdout/stderr or nonzero returncode. If the join in the
            # main thread's stdout loop times out, proc.kill() in its
            # finally block may fire concurrently with a write attempt
            # here — a BrokenPipeError is the expected outcome of that
            # race.
            pass
        except Exception as e:
            writer_error.append(e)
        finally:
            with contextlib.suppress(Exception):
                proc.stdin.close()  # type: ignore[union-attr]

    # SIGINT handling: first Ctrl-C lets the subprocess's own handler
    # run (on Unix it already received the signal via the process
    # group); second Ctrl-C kills the subprocess and re-raises.
    interrupt_count = [0]
    original_handler = signal.getsignal(signal.SIGINT)

    def sigint_handler(signum: int, frame: Any) -> None:
        interrupt_count[0] += 1
        if interrupt_count[0] >= 2:
            signal.signal(signal.SIGINT, original_handler)
            if proc.returncode is None:
                with contextlib.suppress(Exception):
                    proc.kill()
            raise KeyboardInterrupt
        if sys.platform == "win32":
            with contextlib.suppress(Exception):
                proc.send_signal(signal.CTRL_C_EVENT)  # type: ignore[attr-defined]

    signal.signal(signal.SIGINT, sigint_handler)

    writer_thread = threading.Thread(target=stdin_writer, daemon=True)
    writer_thread.start()

    try:
        # Read protocol messages from stdout line by line.
        while True:
            raw = proc.stdout.readline()
            if not raw:
                break
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                # Forward unrecognized lines so nothing is lost. Decode
                # via text sys.stdout (not sys.stdout.buffer) so the
                # path works even when stdout has been wrapped — e.g.,
                # by pytest's capture or by a StringIO harness.
                sys.stdout.write(raw.decode('utf-8', errors='replace'))
                sys.stdout.flush()
                continue

            kind = msg.get('msg')
            if kind == 'log':
                data = msg.get('data', '')
                sys.stdout.write(data if data.endswith('\n') else data + '\n')
                sys.stdout.flush()
            elif kind == 'warning':
                sys.stderr.write(f"Warning: {msg.get('data', '')}\n")
                sys.stderr.flush()
            elif kind == 'error':
                # Record, don't echo: _fail prints it once at the end.
                # Errors are fatal so deferring is fine; warnings are
                # non-fatal and keep streaming live.
                seen_error_from_solver.append(msg.get('data', ''))
            elif kind == 'outputDir' and (path := msg.get('path')):
                print(f"Output directory: {path}")
            # Unknown messages are ignored for forward compatibility.

        writer_thread.join(timeout=_WRITER_JOIN_TIMEOUT)
        try:
            proc.wait(timeout=_PROC_WAIT_TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    finally:
        signal.signal(signal.SIGINT, original_handler)
        if proc.returncode is None:
            with contextlib.suppress(Exception):
                proc.kill()
                proc.wait()

    # Surface any error that blocked clean completion.
    if writer_error:
        _fail(
            f"Error serializing model to benchmark subprocess: {writer_error[0]!r}",
            exit_on_error,
            RuntimeError,
        )

    if seen_error_from_solver:
        _fail(seen_error_from_solver[0], exit_on_error, RuntimeError)

    if proc.returncode != 0:
        _fail(
            f"benchmark subprocess exited with code {proc.returncode}",
            exit_on_error,
            RuntimeError,
        )
