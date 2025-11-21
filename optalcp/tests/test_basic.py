"""
Basic tests for the OptalCP Python API.
"""

import optalcp as cp

def test_simple_interval():
    """Test creating a simple model with an interval variable."""
    model = cp.Model(name="test_simple_interval")

    # Create an interval variable
    x = model.interval_var(length=10, name="x")

    # Add constraints
    model.constraint(x.start() >= 0)
    model.constraint(x.end() <= 100)

    # Set objective
    model.minimize(x.start())

    result = cp.solve(model)

    # Check results
    assert result.nb_solutions > 0, "Should find at least one solution"
    assert result.objective_value == 0, f"Objective should be 0, got {result.objective_value}"

    print(f"✓ test_simple_interval passed: {result}")


def test_interval_precedence():
    """Test precedence constraints between intervals."""
    model = cp.Model(name="test_precedence")

    # Create two intervals
    x = model.interval_var(length=10, name="x")
    y = model.interval_var(length=10, name="y")

    # x must end before y starts
    x.end_before_start(y)

    # Both must be within [0, 100]
    model.constraint(x.start() >= 0)
    model.constraint(y.end() <= 100)

    # Minimize the end time of y
    model.minimize(y.end())

    result = cp.solve(model)

    assert result.nb_solutions > 0, "Should find at least one solution"
    assert result.objective_value == 20, f"Objective should be 20, got {result.objective_value}"

    print(f"✓ test_interval_precedence passed: {result}")


def test_integer_variable():
    """Test integer variables and arithmetic."""
    model = cp.Model(name="test_int_var")

    # Create integer variables
    x = model.int_var(min=0, max=5, name="x")
    y = model.int_var(min=0, max=5, name="y")

    # x + y == 15 (impossible given the domains - max is 10)
    model.constraint(x + y == 15)

    result = cp.solve(model, cp.Parameters(nbWorkers=1))

    # This should be infeasible
    assert result.nb_solutions == 0, "Should be infeasible"
    assert result.proof, "Should prove infeasibility"

    print(f"✓ test_integer_variable passed: {result}")


def test_optional_interval():
    """Test optional interval variables."""
    model = cp.Model(name="test_optional")

    # Create an optional interval
    x = model.interval_var(length=10, optional=True, name="x")

    # If present, must start at 0
    model.constraint(x.start() == 0)

    # Minimize presence (prefer absent)
    model.minimize(x.presence())

    result = cp.solve(model)

    assert result.nb_solutions > 0, "Should find at least one solution"
    # When minimizing presence, the interval should be absent (presence=0)
    assert result.objective_value == 0, f"Objective should be 0, got {result.objective_value}"

    print(f"✓ test_optional_interval passed: {result}")


def test_expression_reuse():
    """Test that expressions used multiple times get reference IDs."""
    model = cp.Model(name="test_reuse")

    x = model.interval_var(length=10, name="x")

    # Use end of x twice
    end = x.end()
    model.minimize(end)
    model.constraint(end <= 100)

    result = cp.solve(model)

    assert result.nb_solutions > 0, "Should find at least one solution"

    # Check that end expression got a reference ID in the model
    model_dict = model._to_dict()
    # The end expression should be in refs since it's used twice
    assert len(model_dict['refs']) > 1, "Should have multiple refs"

    print(f"✓ test_expression_reuse passed: {result}")


def test_orjson_detection():
    """Test that orjson detection works."""
    has_orjson = cp.is_orjson_available()
    print(f"orjson available: {has_orjson}")

    # This test always passes, just reports status
    print(f"✓ test_orjson_detection passed")


def test_iterable_no_overlap():
    """Test that no_overlap accepts various iterable types."""
    model = cp.Model(name="test_iterable_no_overlap")

    # Create tasks
    task1 = model.interval_var(length=10, name="task1")
    task2 = model.interval_var(length=15, name="task2")
    task3 = model.interval_var(length=20, name="task3")

    # Test with tuple (not just list)
    tasks_tuple = (task1, task2, task3)
    model.no_overlap(tasks_tuple)

    model.minimize(model.max([t.end() for t in tasks_tuple]))

    result = cp.solve(model)
    assert result.nb_solutions > 0, "Should find solution with tuple"
    assert result.objective_value == 45, f"Expected 45, got {result.objective_value}"

    print(f"✓ test_iterable_no_overlap passed: tuple accepted")


def test_iterable_no_overlap_with_transitions():
    """Test that no_overlap with transitions accepts iterable transitions."""
    model = cp.Model(name="test_iterable_transitions")

    tasks = [
        model.interval_var(length=10, name="task1"),
        model.interval_var(length=15, name="task2"),
        model.interval_var(length=20, name="task3")
    ]

    # Use tuple of tuples for transitions (not list of lists)
    transitions = (
        (0, 5, 10),
        (5, 0, 5),
        (10, 5, 0)
    )

    model.no_overlap(tasks, transitions)
    model.minimize(model.sum([t.end() for t in tasks]))

    result = cp.solve(model)
    assert result.nb_solutions > 0, "Should find solution with tuple transitions"

    print(f"✓ test_iterable_no_overlap_with_transitions passed")


def test_iterable_step_function():
    """Test that step_function accepts various iterable types."""
    model = cp.Model(name="test_iterable_step_function")

    # Use tuple instead of list
    values_tuple = (
        (1, 10),
        (2, 20),
        (3, 30)
    )

    # Should accept tuple - this tests the iterable functionality
    function = model.step_function(values_tuple)

    # Simple model with objective to test iterable acceptance
    task = model.interval_var(length=5, name="task", start=(0, 25))
    model.minimize(task.start())

    #  Use solution limit for faster testing
    params = cp.Parameters(solutionLimit=1)

    result = cp.solve(model, params=params)
    assert result.nb_solutions > 0, "Should find solution with tuple"

    print(f"✓ test_iterable_step_function passed: tuple accepted")


def test_iterable_generator():
    """Test that functions accept generator expressions."""
    model = cp.Model(name="test_generator")

    # Create tasks
    tasks = [model.interval_var(length=10, name=f"task{i}") for i in range(3)]

    # Use generator expression (most flexible iterable)
    # Note: each generator can only be consumed once
    model.no_overlap((t for t in tasks))

    # Use generator for max
    model.minimize(model.max(t.end() for t in tasks))

    result = cp.solve(model)
    assert result.nb_solutions > 0, "Should find solution with generators"

    print(f"✓ test_iterable_generator passed: generators accepted")


def test_iterable_int_expressions():
    """Test that sum/max accept iterable of expressions."""
    model = cp.Model(name="test_iterable_expressions")

    x = model.interval_var(length=10, name="x")
    y = model.interval_var(length=20, name="y")
    z = model.interval_var(length=15, name="z")

    # Use tuple of expressions
    ends_tuple = (x.end(), y.end(), z.end())

    # max should accept tuple
    model.minimize(model.max(ends_tuple))

    result = cp.solve(model)
    assert result.nb_solutions > 0, "Should find solution"

    print(f"✓ test_iterable_int_expressions passed: tuple of expressions accepted")


def test_min2_basic():
    """Test binary minimum function (min2)."""
    model = cp.Model(name="test_min2")

    x = model.int_var(min=0, max=10, name="x")
    y = model.int_var(min=0, max=10, name="y")

    # min2(x, y) should return the minimum
    z = model.min2(x, y)

    # Force x=7, y=3, then min2 should be 3
    model.constraint(x == 7)
    model.constraint(y == 3)
    model.minimize(z)

    params = cp.Parameters(solutionLimit=1)
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find solution"
    assert result.objective_value == 3, f"min2(7, 3) should be 3, got {result.objective_value}"

    print(f"✓ test_min2_basic passed: min2(7, 3) = {result.objective_value}")


def test_max2_basic():
    """Test binary maximum function (max2)."""
    model = cp.Model(name="test_max2")

    x = model.int_var(min=0, max=10, name="x")
    y = model.int_var(min=0, max=10, name="y")

    # max2(x, y) should return the maximum
    z = model.max2(x, y)

    # Force x=7, y=3, then max2 should be 7
    model.constraint(x == 7)
    model.constraint(y == 3)
    model.minimize(z)

    params = cp.Parameters(solutionLimit=1)
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find solution"
    assert result.objective_value == 7, f"max2(7, 3) should be 7, got {result.objective_value}"

    print(f"✓ test_max2_basic passed: max2(7, 3) = {result.objective_value}")


def test_min2_with_constants():
    """Test min2 with constants."""
    model = cp.Model(name="test_min2_const")

    x = model.int_var(min=0, max=10, name="x")

    # min2(x, 5) - should clamp x to at most 5
    z = model.min2(x, 5)

    # Maximize x (try to push it high)
    model.maximize(z)

    result = cp.solve(model)

    assert result.nb_solutions >= 1, "Should find solution"
    assert result.objective_value == 5, f"max(min2(x, 5)) should be 5, got {result.objective_value}"

    print(f"✓ test_min2_with_constants passed: max(min2(x, 5)) = {result.objective_value}")


def test_max2_with_constants():
    """Test max2 with constants."""
    model = cp.Model(name="test_max2_const")

    x = model.int_var(min=0, max=10, name="x")

    # max2(x, 5) - should clamp x to at least 5
    z = model.max2(x, 5)

    # Minimize z (try to push it low)
    model.minimize(z)

    # Don't use SolutionLimit for optimization - let solver find optimal
    result = cp.solve(model)

    assert result.nb_solutions >= 1, "Should find solution"
    assert result.objective_value == 5, f"min(max2(x, 5)) should be 5, got {result.objective_value}"

    print(f"✓ test_max2_with_constants passed: min(max2(x, 5)) = {result.objective_value}")


def test_min2_max2_combination():
    """Test combination of min2 and max2 (clamping)."""
    model = cp.Model(name="test_clamp")

    x = model.int_var(min=-10, max=20, name="x")

    # Clamp x to [5, 10]: max2(5, min2(x, 10))
    clamped = model.max2(5, model.min2(x, 10))

    model.constraint(x == 15)
    model.minimize(clamped)

    params = cp.Parameters(solutionLimit=1)
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find solution"
    # x=15, min2(15, 10)=10, max2(5, 10)=10
    assert result.objective_value == 10, f"Clamped value should be 10, got {result.objective_value}"

    print(f"✓ test_min2_max2_combination passed: clamp(15, 5, 10) = {result.objective_value}")


def test_min2_with_intervals():
    """Test min2 with interval start/end times."""
    model = cp.Model(name="test_min2_intervals")

    x = model.interval_var(start=(0, 100), length=10, name="x")
    y = model.interval_var(start=(0, 100), length=10, name="y")

    # Find minimum end time
    min_end = model.min2(x.end(), y.end())

    model.minimize(min_end)

    params = cp.Parameters(solutionLimit=1)
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find solution"
    assert result.objective_value == 10, f"Minimum end time should be 10, got {result.objective_value}"

    print(f"✓ test_min2_with_intervals passed: min end time = {result.objective_value}")


def test_max2_with_intervals():
    """Test max2 with interval start/end times."""
    model = cp.Model(name="test_max2_intervals")

    x = model.interval_var(start=(0, 100), length=10, name="x")
    y = model.interval_var(start=(0, 100), length=10, name="y")

    # Find maximum end time (makespan)
    makespan = model.max2(x.end(), y.end())

    # Force specific positions
    model.constraint(x.start() == 0)  # x: [0, 10]
    model.constraint(y.start() == 5)  # y: [5, 15]

    model.minimize(makespan)

    params = cp.Parameters(solutionLimit=1)
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find solution"
    assert result.objective_value == 15, f"Makespan should be 15, got {result.objective_value}"

    print(f"✓ test_max2_with_intervals passed: makespan = {result.objective_value}")
