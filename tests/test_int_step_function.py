"""
Tests for IntStepFunction class.

Note: These tests require Model.step_function() and related methods to be implemented.
"""

import pytest
import optalcp as cp


def test_step_function_creation():
    """Test creating an integer step function."""

    model = cp.Model()

    # Create a simple step function
    # At point 0, value is 1; at point 10, value changes to 0; at point 20, value changes to 2
    function = model.step_function([
        (0, 1),
        (10, 0),
        (20, 2)
    ])

    # Verify it's the right type
    assert isinstance(function, cp.IntStepFunction)


def test_step_function_validation():
    """Test that step function validates input."""

    model = cp.Model()

    # Test that values cannot be a string (common user error - iterates over characters)
    with pytest.raises(ValueError, match=r"must have exactly 2 elements .* got 1: 'n'"):
        model.step_function("not a list")

    # Test that items must have exactly 2 elements
    with pytest.raises(ValueError, match="must have exactly 2 elements"):
        model.step_function([(1,)])

    with pytest.raises(ValueError, match="must have exactly 2 elements"):
        model.step_function([(1, 2, 3)])

    # Test that both x and y must be integers
    with pytest.raises(TypeError, match="must be an integer"):
        model.step_function([(1.5, 10)])  # x must be int

    with pytest.raises(TypeError, match="must be an integer"):
        model.step_function([(1, 10.5)])  # y must be int

    with pytest.raises(TypeError, match="must be an integer"):
        model.step_function([("a", 10)])  # x must be int


def test_step_function_calendar_example():
    """Test step function as a calendar with allowed/forbidden times."""

    model = cp.Model(name="StepFunctionCalendarExample")

    # Create a calendar where 0=forbidden (weekend), 1=allowed (weekday)
    # Format: (point, value) - at each point, the value changes
    calendar = model.step_function([
        (0, 1),    # At day 0 (Mon), value=1 (allowed)
        (5, 0),    # At day 5 (Sat), value=0 (forbidden)
        (7, 1),    # At day 7 (next Mon), value=1 (allowed)
        (12, 0),   # At day 12 (next Sat), value=0 (forbidden)
    ])

    # Create a task that starts in weekend
    task = model.interval_var(length=1, start=(5, 20), name="task")

    # Task cannot start during weekend (when calendar value is 0)
    model.forbid_start(task, calendar)
    model.minimize(task.start())

    # Solve and verify task doesn't start on weekend
    params = cp.Parameters(solutionLimit=1)
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find solution"
    # Task should start at day 7 (first allowed day after day 5)
    assert result.best_solution.get_start(task) == 7


def test_step_function_eval():
    """Test evaluating a step function at a point."""
    model = cp.Model()

    # Create a step function: (point, value)
    # At point 0: value=1, at point 10: value=0, at point 20: value=2
    function = model.step_function([
        (0, 1),   # value=1 from 0 to 10
        (10, 0),  # value=0 from 10 to 20
        (20, 2)   # value=2 from 20 onwards
    ])

    # Create an interval variable starting at 15
    x = model.interval_var(length=5, start=(15, 15), name="x")

    # Evaluate the function at the start of x (which is 15)
    val = model.step_function_eval(function, x.start())

    # val should be an IntExpr
    assert isinstance(val, cp.IntExpr)

    # Constrain that evaluated value equals 0 (since at x=15, function value is 0)
    model.constraint(val == 0)

    # Solve to verify
    params = cp.Parameters(solutionLimit=1)
    result = cp.solve(model, params=params)
    assert result.nb_solutions == 1


def test_step_function_sum():
    """Test computing sum (integral) of a step function over an interval."""

    model = cp.Model()

    # Create a step function representing cost per time unit (point, value)
    # At hour 0: cost=10, at hour 8: cost=20, at hour 17: cost=10
    cost_function = model.step_function([
        (0, 10),    # Cost 10 during hours 0-8 (night rate)
        (8, 20),    # Cost 20 during hours 8-17 (day rate)
        (17, 10)    # Cost 10 during hours 17-24 (evening rate)
    ])

    # Create a task that can be scheduled anywhere
    task = model.interval_var(length=3, start=(0, 24), name="task")

    # Compute the total cost as the integral of cost_function over task
    total_cost = model.step_function_sum(cost_function, task)

    # Minimize the total cost (should schedule during night: 0-8 or evening: 17-24)
    model.minimize(total_cost)

    params = cp.Parameters(solutionLimit=1)
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find solution"
    # Minimum cost for 3 hours should be 30 (3 hours * 10 per hour)
    assert result.objective_value == 30


def test_step_function_forbid_start():
    """Test forbidding start times using a step function."""
    model = cp.Model()

    # Create a calendar: 1=allowed, 0=forbidden (point, value)
    calendar = model.step_function([
        (0, 1),   # Allowed from 0 to 10
        (10, 0),  # Forbidden from 10 to 15
        (15, 1)   # Allowed from 15 to 30
    ])

    task = model.interval_var(length=5, start=(0, 30), name="task")

    # Task cannot start during forbidden times [10, 15)
    model.forbid_start(task, calendar)
    model.minimize(task.start())

    params = cp.Parameters(solutionLimit=1)
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find solution"
    # Should start at 0 (first allowed position)
    assert result.best_solution.get_start(task) == 0


def test_step_function_forbid_end():
    """Test forbidding end times using a step function."""

    model = cp.Model()

    # Create a calendar: 1=allowed, 0=forbidden (point, value)
    calendar = model.step_function([
        (0, 1),   # Allowed from 0 to 10
        (10, 0),  # Forbidden from 10 to 15
        (15, 1)   # Allowed from 15 to 30
    ])

    task = model.interval_var(length=5, start=(0, 30), name="task")

    # Task cannot end during forbidden times [10, 15)
    model.forbid_end(task, calendar)
    model.minimize(task.end())

    params = cp.Parameters(solutionLimit=1)
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find solution"
    # Should end at 5 (within allowed zone [0, 10))
    assert result.best_solution.get_end(task) == 5


def test_step_function_forbid_extent():
    """Test forbidding extent using a step function."""

    model = cp.Model()

    # Create a calendar: 1=allowed, 0=forbidden (point, value)
    calendar = model.step_function([
        (0, 1),   # Allowed from 0 to 10
        (10, 0),  # Forbidden from 10 to 15
        (15, 1)   # Allowed from 15 to 30
    ])

    task = model.interval_var(length=5, start=(0, 30), name="task")

    # Task extent [start, end) cannot overlap forbidden times [10, 15)
    model.forbid_extent(task, calendar)
    model.minimize(task.start())

    params = cp.Parameters(solutionLimit=1)
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find solution"
    # Should start at 0 to end at 5 (entirely in allowed zone [0, 10))
    assert result.best_solution.get_start(task) == 0
    assert result.best_solution.get_end(task) == 5


def test_step_function_with_tuples():
    """Test that step function accepts tuples as well as lists."""

    model = cp.Model()

    # Should accept tuples (point, value)
    function = model.step_function([
        (0, 1),
        (10, 0),
        (20, 2)
    ])

    assert isinstance(function, cp.IntStepFunction)


def test_step_function_with_lists():
    """Test that step function accepts lists for items."""

    model = cp.Model()

    # Should accept lists for individual items (point, value)
    function = model.step_function([
        [0, 1],
        [10, 0],
        [20, 2]
    ])

    assert isinstance(function, cp.IntStepFunction)


def test_step_function_empty():
    """Test creating an empty step function."""

    model = cp.Model()

    # Empty function should be allowed
    function = model.step_function([])
    assert isinstance(function, cp.IntStepFunction)


def test_step_function_single_value():
    """Test creating a step function with a single value."""

    model = cp.Model()

    # Single value step function
    function = model.step_function([(5, 100)])

    assert isinstance(function, cp.IntStepFunction)


def test_step_function_negative_values():
    """Test that step function accepts negative values."""

    model = cp.Model()

    # Should accept negative values and points
    function = model.step_function([
        (-10, -5),
        (0, 0),
        (10, 5)
    ])

    assert isinstance(function, cp.IntStepFunction)


def test_step_function_large_values():
    """Test step function with large integer values."""

    model = cp.Model()

    # Should handle large values within IntVar range
    function = model.step_function([
        (0, cp.IntVarMin),
        (1, 0),
        (0, cp.IntVarMax)
    ])

    assert isinstance(function, cp.IntStepFunction)
