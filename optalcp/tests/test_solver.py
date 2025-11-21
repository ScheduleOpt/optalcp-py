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
