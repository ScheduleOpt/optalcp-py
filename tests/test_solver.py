"""
Tests for the async Solver class with event handlers.
"""

import asyncio
import pytest
import optalcp as cp
from optalcp import Solver

class RunResults:
    """Helper class to collect test results."""
    def __init__(self):
        self.logs: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.solutions: list[cp.SolutionEvent] = []
        self.lower_bounds: list[cp.LowerBoundEntry] = []

    def reset(self):
        self.logs.clear()
        self.warnings.clear()
        self.errors.clear()
        self.solutions.clear()
        self.lower_bounds.clear()

@pytest.mark.asyncio
async def test_callbacks_via_constructor():
    """Test setting callbacks via constructor parameters."""

    results = RunResults()

    solver = Solver()
    solver.output_stream = None  # Disable output for tests
    solver.on_log = lambda msg: results.logs.append(msg)
    solver.on_warning = lambda msg: results.warnings.append(msg)
    solver.on_error = lambda msg: results.errors.append(msg)
    solver.on_solution = lambda sol: results.solutions.append(sol)

    # Simple model
    model = cp.Model(name='test')
    x = model.interval_var(length=10, name='x')
    model.minimize(x.start())

    result = await solver.solve(model)

    # Check that we got callbacks
    assert len(results.solutions) > 0, "Should have received at least one solution"
    assert result.nb_solutions > 0, "Should have found at least one solution"

    print(f"  ✓ Received {len(results.solutions)} solution event(s)")
    print(f"  ✓ Result: {result}")
    return True

@pytest.mark.asyncio
async def test_callbacks_via_attributes():
    """Test setting callbacks as public attributes."""

    results = RunResults()

    solver = Solver()
    solver.output_stream = None  # Disable output for tests
    solver.on_solution = lambda sol: results.solutions.append(sol)
    solver.on_log = lambda msg: results.logs.append(msg)

    # Simple model
    model = cp.Model(name='test')
    x = model.interval_var(length=10, name='x')
    model.minimize(x.start())

    result = await solver.solve(model)

    assert len(results.solutions) > 0, "Should have received at least one solution"
    assert result.nb_solutions > 0, "Should have found at least one solution"

    print(f"  ✓ Received {len(results.solutions)} solution event(s)")
    print(f"  ✓ Result: {result}")
    return True


@pytest.mark.asyncio
async def test_multiple_solvers_parallel():
    """Test running multiple solvers in parallel."""

    results1 = RunResults()
    results2 = RunResults()

    # Disable output for tests
    solver1 = Solver()
    solver1.output_stream = None
    solver1.on_solution = lambda s: results1.solutions.append(s)

    solver2 = Solver()
    solver2.output_stream = None
    solver2.on_solution = lambda s: results2.solutions.append(s)

    # Create two different models
    model1 = cp.Model(name='model1')
    x1 = model1.interval_var(length=10, name='x1')
    model1.minimize(x1.start())

    model2 = cp.Model(name='model2')
    x2 = model2.interval_var(length=20, name='x2')
    model2.minimize(x2.start())

    # Run both solvers in parallel
    task1 = asyncio.create_task(solver1.solve(model1))
    task2 = asyncio.create_task(solver2.solve(model2))

    result1, result2 = await asyncio.gather(task1, task2)

    assert len(results1.solutions) > 0, "Solver 1 should have received solutions"
    assert len(results2.solutions) > 0, "Solver 2 should have received solutions"
    assert result1.nb_solutions > 0, "Solver 1 should have found solutions"
    assert result2.nb_solutions > 0, "Solver 2 should have found solutions"

    print(f"  ✓ Solver 1: {len(results1.solutions)} solution(s), result: {result1}")
    print(f"  ✓ Solver 2: {len(results2.solutions)} solution(s), result: {result2}")
    return True


@pytest.mark.asyncio
async def test_no_callbacks():
    """Test that solver works without any callbacks set (output disabled for test)."""

    # Disable output for clean test run
    solver = Solver()
    solver.output_stream = None

    # Simple model
    model = cp.Model(name='test')
    x = model.interval_var(length=10, name='x')
    model.minimize(x.start())

    result = await solver.solve(model)

    assert result.nb_solutions > 0, "Should have found at least one solution"

    print(f"  ✓ Result: {result}")
    return True


@pytest.mark.asyncio
async def test_default_output_stream():
    """Test that default output_stream (stdout) works."""

    # Use default output_stream (sys.stdout)
    solver = Solver()

    # Simple model
    model = cp.Model(name='test_defaults')
    x = model.interval_var(length=5, name='x')
    model.minimize(x.start())

    result = await solver.solve(model)

    assert result.nb_solutions > 0, "Should have found at least one solution"

    print(f"  ✓ Default output stream test completed: {result}")
    return True


@pytest.mark.asyncio
async def test_output_stream_with_handlers():
    """Test that handlers are called even when output_stream is set."""

    results = RunResults()

    import io
    buffer = io.StringIO()

    # Set output_stream AND handlers - both should work
    solver = Solver()
    solver.output_stream = buffer
    solver.on_log = lambda msg: results.logs.append(msg)
    solver.on_solution = lambda sol: results.solutions.append(sol)

    # Simple model
    model = cp.Model(name='test_both')
    x = model.interval_var(length=5, name='x')
    model.minimize(x.start())

    result = await solver.solve(model)

    assert result.nb_solutions > 0, "Should have found at least one solution"
    assert len(results.solutions) > 0, "Handler should have been called"
    assert len(results.logs) > 0, "Log handler should have been called"

    buffer_content = buffer.getvalue()
    assert len(buffer_content) > 0, "Output should have been written to buffer"

    print(f"  ✓ Handlers called: {len(results.solutions)} solutions, {len(results.logs)} logs")
    print(f"  ✓ Buffer received {len(buffer_content)} characters")
    print(f"  ✓ Result: {result}")
    return True


@pytest.mark.asyncio
async def test_solution_event_type():
    """Test that SolutionEvent type works correctly with type annotations."""

    results = RunResults()

    # User function with proper type annotation
    def my_solution_handler(event: cp.SolutionEvent) -> None:
        """Example handler with SolutionEvent type annotation."""
        # Access event fields
        assert 'solveTime' in event, "SolutionEvent should have solveTime"
        assert 'solution' in event, "SolutionEvent should have solution"
        assert isinstance(event['solveTime'], float), "solveTime should be float"
        assert isinstance(event['solution'], cp.Solution), "solution should be Solution object"

        # 'valid' field is optional
        if 'valid' in event:
            assert isinstance(event['valid'], bool), "valid should be bool if present"

        results.solutions.append(event)

    solver = cp.Solver()
    solver.on_solution = my_solution_handler
    solver.output_stream = None

    # Simple model
    model = cp.Model()
    x = model.interval_var(length=10, name='x')
    y = model.interval_var(length=20, name='y')
    x.end_before_start(y)
    model.minimize(y.end())

    result = await solver.solve(model)

    assert len(results.solutions) > 0, "Should have received at least one SolutionEvent"

    # Verify we can access solution values
    event = results.solutions[-1]
    solution = event['solution']
    assert solution.is_present(x), "x should be present"
    assert solution.is_present(y), "y should be present"

    print(f"  ✓ Received {len(results.solutions)} SolutionEvent(s)")
    print(f"  ✓ Last solution at {event['solveTime']:.3f}s")
    print(f"  ✓ Objective: {solution.get_objective()}")
    return True


@pytest.mark.asyncio
async def test_lower_bound_event_type():
    """Test that LowerBoundEntry type works correctly with type annotations."""

    results = RunResults()

    # User function with proper type annotation
    def my_lower_bound_handler(event: cp.LowerBoundEntry) -> None:
        """Example handler with LowerBoundEntry type annotation."""
        # Access event fields
        assert 'solveTime' in event, "LowerBoundEntry should have solveTime"
        assert 'value' in event, "LowerBoundEntry should have value"
        assert isinstance(event['solveTime'], float), "solveTime should be float"
        # value can be float or list for multi-objective
        assert isinstance(event['value'], (float, int, list)), "value should be numeric or list"

        results.lower_bounds.append(event)

    solver = cp.Solver()
    solver.on_lower_bound = my_lower_bound_handler
    solver.output_stream = None

    # Optimization model to generate lower bounds
    model = cp.Model()
    x = model.interval_var(length=10, name='x')
    y = model.interval_var(length=20, name='y')
    x.end_before_start(y)
    model.minimize(y.end())

    result = await solver.solve(model)

    # Lower bounds may or may not be generated depending on solver strategy
    print(f"  ✓ Received {len(results.lower_bounds)} LowerBoundEntry(s)")
    if len(results.lower_bounds) > 0:
        event = results.lower_bounds[-1]
        print(f"  ✓ Last lower bound at {event['solveTime']:.3f}s: {event['value']}")

    return True


@pytest.mark.asyncio
async def test_event_types_structure():
    """Test the TypedDict structure of event types."""

    # Check that the types are available
    assert hasattr(cp, 'SolutionEvent'), "SolutionEvent should be exported"
    assert hasattr(cp, 'LowerBoundEntry'), "LowerBoundEntry should be exported"

    # Check annotations
    solution_annotations = cp.SolutionEvent.__annotations__
    assert 'solveTime' in solution_annotations, "SolutionEvent should define solveTime"
    assert 'valid' in solution_annotations, "SolutionEvent should define valid"
    assert 'solution' in solution_annotations, "SolutionEvent should define solution"

    lower_bound_annotations = cp.LowerBoundEntry.__annotations__
    assert 'solveTime' in lower_bound_annotations, "LowerBoundEntry should define solveTime"
    assert 'value' in lower_bound_annotations, "LowerBoundEntry should define value"

    print("  ✓ SolutionEvent structure verified")
    print(f"    Fields: {list(solution_annotations.keys())}")
    print("  ✓ LowerBoundEntry structure verified")
    print(f"    Fields: {list(lower_bound_annotations.keys())}")

    return True


@pytest.mark.asyncio
async def test_event_types_in_subclass():
    """Test using event types in a subclass with proper annotations."""

    class TypedSolver(cp.Solver):
        """Solver subclass with typed event handlers."""
        def __init__(self):
            super().__init__()
            self.output_stream = None
            self.solution_times = []
            self.lower_bound_values = []

        def on_solution(self, event: cp.SolutionEvent) -> None:
            """Typed solution handler."""
            self.solution_times.append(event['solveTime'])

        def on_lower_bound(self, event: cp.LowerBoundEntry) -> None:
            """Typed lower bound handler."""
            self.lower_bound_values.append(event['value'])

    solver = TypedSolver()

    # Simple optimization model
    model = cp.Model()
    x = model.interval_var(length=10, name='x')
    model.minimize(x.start())

    result = await solver.solve(model)

    assert len(solver.solution_times) > 0, "Should have received solutions"
    assert result.nb_solutions > 0, "Should have found solutions"

    print(f"  ✓ TypedSolver received {len(solver.solution_times)} solution(s)")
    print(f"  ✓ TypedSolver received {len(solver.lower_bound_values)} lower bound(s)")

    return True

@pytest.mark.asyncio
async def test_on_summary_callback():
    """Test that on_summary callback receives SolveSummary with all fields."""
    summaries = []

    def handle_summary(summary: cp.SolveSummary) -> None:
        """Capture summary for inspection."""
        summaries.append(summary)

    solver = cp.Solver()
    solver.on_summary = handle_summary
    solver.output_stream = None

    # Simple optimization model
    model = cp.Model()
    x = model.interval_var(length=10, name='x')
    y = model.interval_var(length=20, name='y')
    x.end_before_start(y)
    model.minimize(y.end())

    result = await solver.solve(model)

    # Should have received exactly one summary
    assert len(summaries) == 1, "Should receive exactly one summary"

    summary = summaries[0]

    # Check core fields
    assert 'nbSolutions' in summary, "Summary should have nbSolutions"
    assert 'duration' in summary, "Summary should have duration"
    assert 'nbBranches' in summary, "Summary should have nbBranches"
    assert 'nbFails' in summary, "Summary should have nbFails"

    # Check additional fields
    assert 'nbLNSSteps' in summary, "Summary should have nbLNSSteps"
    assert 'memoryUsed' in summary, "Summary should have memoryUsed"
    assert 'solver' in summary, "Summary should have solver version"
    assert 'nbWorkers' in summary, "Summary should have nbWorkers"

    # Summary values should match result
    assert summary['nbSolutions'] == result.nb_solutions

    print(f"  ✓ on_summary callback received SolveSummary")
    print(f"  ✓ Summary has {len(summary)} fields")
    print(f"  ✓ Solver: {summary.get('solver', 'N/A')}")
    print(f"  ✓ Workers: {summary.get('nbWorkers', 0)}")

    return True


@pytest.mark.asyncio
async def test_solve_result_has_all_fields():
    """Test that SolveResult exposes all new fields."""
    solver = cp.Solver()
    solver.output_stream = None

    model = cp.Model()
    x = model.interval_var(length=10, name='x')
    model.minimize(x.start())

    result = await solver.solve(model)

    # Check existing fields still work
    assert result.nb_solutions > 0
    assert result.duration > 0
    assert result.nb_branches >= 0

    # Check new SolveSummary fields
    assert hasattr(result, 'nb_lns_steps')
    assert hasattr(result, 'nb_restarts')
    assert hasattr(result, 'memory_used')
    assert hasattr(result, 'nb_int_vars')
    assert hasattr(result, 'nb_interval_vars')
    assert hasattr(result, 'nb_constraints')
    assert hasattr(result, 'solver')
    assert hasattr(result, 'nb_workers')
    assert hasattr(result, 'cpu')
    assert hasattr(result, 'objective_sense')

    # Check tracking fields
    assert hasattr(result, 'objective_history')
    assert hasattr(result, 'lower_bound_history')
    assert hasattr(result, 'best_solution_time')
    assert hasattr(result, 'best_lb_time')
    assert hasattr(result, 'best_solution_valid')

    print(f"  ✓ SolveResult has all SolveSummary fields")
    print(f"  ✓ Solver: {result.solver}")
    print(f"  ✓ Memory: {result.memory_used} bytes")
    print(f"  ✓ Workers: {result.nb_workers}")
    print(f"  ✓ Variables: {result.nb_int_vars} int, {result.nb_interval_vars} interval")
    print(f"  ✓ Objective sense: {result.objective_sense}")

    return True


@pytest.mark.asyncio
async def test_objective_history_tracking():
    """Test that objective history is tracked correctly."""
    solver = cp.Solver()
    solver.output_stream = None

    model = cp.Model()
    x = model.interval_var(length=10, name='x')
    y = model.interval_var(length=20, name='y')
    x.end_before_start(y)
    model.minimize(y.end())

    result = await solver.solve(model)

    # Should have objective history
    assert len(result.objective_history) > 0, "Should have at least one entry in objective history"

    # Each entry should have required fields
    for entry in result.objective_history:
        assert 'solveTime' in entry, "History entry should have solveTime"
        assert 'objective' in entry, "History entry should have objective"
        assert 'valid' in entry, "History entry should have valid"

    # Best solution time should be set
    assert result.best_solution_time is not None, "best_solution_time should be set"

    # Last entry should match best solution
    last_entry = result.objective_history[-1]
    assert last_entry['objective'] == result.objective_value

    print(f"  ✓ Tracked {len(result.objective_history)} objective improvement(s)")
    print(f"  ✓ Best solution at {result.best_solution_time:.3f}s")
    print(f"  ✓ Final objective: {result.objective_value}")

    return True


@pytest.mark.asyncio
async def test_type_exports():
    """Test that new types are exported correctly."""
    # Should be able to import types
    assert hasattr(cp, 'SolveSummary'), "SolveSummary should be exported"
    assert hasattr(cp, 'ObjectiveEntry'), "ObjectiveEntry should be exported"
    assert hasattr(cp, 'LowerBoundEntry'), "LowerBoundEntry should be exported"

    # Check annotations
    summary_annotations = cp.SolveSummary.__annotations__
    assert 'nbSolutions' in summary_annotations
    assert 'nbBranches' in summary_annotations
    assert 'nbLNSSteps' in summary_annotations
    assert 'memoryUsed' in summary_annotations
    assert 'solver' in summary_annotations

    history_annotations = cp.ObjectiveEntry.__annotations__
    assert 'solveTime' in history_annotations
    assert 'objective' in history_annotations
    assert 'valid' in history_annotations

    lb_annotations = cp.LowerBoundEntry.__annotations__
    assert 'solveTime' in lb_annotations
    assert 'value' in lb_annotations

    print("  ✓ SolveSummary type exported and verified")
    print("  ✓ ObjectiveEntry type exported and verified")
    print("  ✓ LowerBoundEntry type exported and verified")

    return True


@pytest.mark.asyncio
async def test_async_event_handlers():
    """Test that event handlers can be async functions."""

    results = RunResults()
    call_order = []

    # Async event handlers that simulate some async work
    async def async_solution_handler(event: cp.SolutionEvent) -> None:
        """Async solution handler that does some async work."""
        solve_time = event.get('solveTime', 0.0)
        call_order.append(('solution_start', solve_time))
        # Simulate async work (e.g., writing to database, API call, etc.)
        await asyncio.sleep(0.01)
        results.solutions.append(event)
        call_order.append(('solution_end', solve_time))

    async def async_log_handler(msg: str) -> None:
        """Async log handler."""
        call_order.append(('log_start', len(results.logs)))
        await asyncio.sleep(0.001)
        results.logs.append(msg)
        call_order.append(('log_end', len(results.logs)))

    async def async_summary_handler(summary: cp.SolveSummary) -> None:
        """Async summary handler."""
        call_order.append('summary_start')
        await asyncio.sleep(0.005)
        call_order.append('summary_end')

    solver = cp.Solver()
    solver.output_stream = None
    solver.on_solution = async_solution_handler  # type: ignore[assignment]
    solver.on_log = async_log_handler  # type: ignore[assignment]
    solver.on_summary = async_summary_handler  # type: ignore[assignment]

    # Create a job shop model that will find multiple solutions
    # This is a simplified version of the la17 problem from interactiveJobshop.ts
    model = cp.Model(name='jobshop')
    nb_machines = 3

    # Job shop data: [machine_id, duration] pairs for each operation
    # 3 jobs, 3 operations each
    jobs_data = [
        [0, 10, 1, 20, 2, 15],  # Job 0
        [1, 15, 2, 10, 0, 25],  # Job 1
        [2, 20, 0, 15, 1, 10],  # Job 2
    ]

    machines: list[list[cp.IntervalVar]] = [[] for _ in range(nb_machines)]
    ends: list[cp.IntExpr] = []

    for job_id, job_ops in enumerate(jobs_data):
        prev: cp.IntervalVar | None = None
        for op_id in range(nb_machines):
            machine_id = job_ops[op_id * 2]
            duration = job_ops[op_id * 2 + 1]
            operation = model.interval_var(
                length=duration,
                name=f'J{job_id}O{op_id}M{machine_id}'
            )
            machines[machine_id].append(operation)
            if prev is not None:
                prev.end_before_start(operation)
            prev = operation
        if prev is not None:
            ends.append(prev.end())

    # No overlap on each machine
    for machine in machines:
        model.no_overlap(machine)

    # Minimize makespan
    model.minimize(model.max(ends))

    # Solve with a short time limit and solution limit
    params = cp.Parameters(timeLimit=2000)
    result = await solver.solve(model, params=params)

    # Verify that async handlers were called
    assert len(results.solutions) > 0, "Should have received at least one solution"
    assert len(results.logs) > 0, "Should have received log messages"
    assert result.nb_solutions > 0, "Should have found at least one solution"

    # Verify that async work happened (we should see interleaved start/end calls)
    assert len(call_order) > 0, "Call order should be recorded"

    # Check that we have both start and end events for solutions
    solution_starts = [x for x in call_order if x[0] == 'solution_start']
    solution_ends = [x for x in call_order if x[0] == 'solution_end']
    assert len(solution_starts) == len(solution_ends), "Each solution start should have an end"
    assert len(solution_starts) == len(results.solutions), "Should match number of solutions"

    print(f"  ✓ Async solution handler called {len(results.solutions)} time(s)")
    print(f"  ✓ Async log handler called {len(results.logs)} time(s)")
    print(f"  ✓ Call order shows {len(call_order)} async operations")
    print(f"  ✓ Result: {result}")

    return True


@pytest.mark.asyncio
async def test_mixed_sync_async_handlers():
    """Test that sync and async handlers can be mixed."""

    results = RunResults()
    sync_calls = []
    async_calls = []

    # Mix of sync and async handlers
    def sync_log_handler(msg: str) -> None:
        """Synchronous log handler."""
        sync_calls.append('log')
        results.logs.append(msg)

    async def async_solution_handler(event: cp.SolutionEvent) -> None:
        """Async solution handler."""
        async_calls.append('solution')
        await asyncio.sleep(0.001)
        results.solutions.append(event)

    def sync_summary_handler(summary: cp.SolveSummary) -> None:
        """Synchronous summary handler."""
        sync_calls.append('summary')

    solver = cp.Solver()
    solver.output_stream = None
    solver.on_log = sync_log_handler  # Sync
    solver.on_solution = async_solution_handler  # type: ignore[assignment] # Async
    solver.on_summary = sync_summary_handler  # Sync

    # Simple model
    model = cp.Model()
    x = model.interval_var(length=10, name='x')
    model.minimize(x.start())

    await solver.solve(model)

    # Both sync and async handlers should have been called
    assert len(sync_calls) > 0, "Sync handlers should have been called"
    assert len(async_calls) > 0, "Async handlers should have been called"
    assert len(results.solutions) > 0, "Async solution handler should have collected solutions"
    assert len(results.logs) > 0, "Sync log handler should have collected logs"

    print(f"  ✓ Sync handlers called {len(sync_calls)} time(s)")
    print(f"  ✓ Async handlers called {len(async_calls)} time(s)")
    print(f"  ✓ Mixed sync/async handlers work correctly")

    return True

@pytest.mark.asyncio
async def test_async_callback_exception_propagation():
    """Test that async callback exceptions propagate immediately."""
    import time

    # Use infeasible model that would run forever without time limit
    model = cp.Model()
    x = model.int_var(name="x")
    y = model.int_var(name="y")
    model.constraint(x < y)
    model.constraint(y < x)

    start_time = time.time()
    exception_raised = False

    async def bad_handler(msg):
        # Raise exception immediately when first log message arrives
        raise ValueError("Async callback error!")

    solver = cp.Solver()
    solver.output_stream = None
    solver.on_log = bad_handler

    try:
        params = cp.Parameters(timeLimit=10)  # 10 seconds if exception doesn't work
        result = await solver.solve(model, params=params)
        assert False, "Should have raised exception"
    except (ValueError, ExceptionGroup, BaseExceptionGroup) as e:
        exception_raised = True
        elapsed = time.time() - start_time
        print(f"  ✓ Exception caught: {type(e).__name__}")
        print(f"  ✓ Time elapsed: {elapsed:.2f}s")
        assert elapsed < 2.0, f"Exception took too long to propagate: {elapsed:.2f}s"
        print(f"  ✓ Exception propagated immediately (< 2s, not 10s)")

    assert exception_raised, "Exception should have been raised"
    return True

@pytest.mark.asyncio
async def test_sync_callback_exception_propagation():
    """Test that sync callback exceptions propagate immediately."""
    import time

    # Use infeasible model that would run forever without time limit
    model = cp.Model()
    x = model.int_var(name="x")
    y = model.int_var(name="y")
    model.constraint(x < y)
    model.constraint(y < x)

    start_time = time.time()
    exception_raised = False

    def bad_handler(msg):
        # Raise exception immediately when first log message arrives
        raise ValueError("Sync callback error!")

    solver = cp.Solver()
    solver.output_stream = None
    solver.on_log = bad_handler

    try:
        params = cp.Parameters(timeLimit=10)  # 10 seconds if exception doesn't work
        result = await solver.solve(model, params=params)
        assert False, "Should have raised exception"
    except (ValueError, ExceptionGroup, BaseExceptionGroup) as e:
        exception_raised = True
        elapsed = time.time() - start_time
        print(f"  ✓ Exception caught: {type(e).__name__}")
        print(f"  ✓ Time elapsed: {elapsed:.2f}s")
        assert elapsed < 2.0, f"Exception took too long to propagate: {elapsed:.2f}s"
        print(f"  ✓ Exception propagated immediately (< 2s, not 10s)")

    assert exception_raised, "Exception should have been raised"
    return True
