#!/usr/bin/env python3
"""
Tests for Solution class functionality.

Tests cover:
- Querying variable values from solutions
- Checking presence/absence of optional variables
- Getting objective values
- Creating warm starts manually
- Solving with warm starts
- Accessing solutions in callbacks
"""

import pytest
import optalcp as cp


def test_basic_solution_query():
    """Test querying values from a solved model."""
    print("Test: Basic solution query")

    model = cp.Model()

    # Create variables
    x = model.interval_var(length=10, name="x")
    y = model.interval_var(length=20, name="y")

    # Add constraints
    model.constraint(x.start() >= 0)
    model.constraint(x.end() <= 100)
    x.end_before_start(y)

    # Minimize completion time
    model.minimize(y.end())

    # Solve
    result = cp.solve(model)

    print(f"  Found {result.nb_solutions} solution(s)")
    print(f"  Objective: {result.objective_value}")

    # Check solution exists
    assert result.best_solution is not None, "Expected a solution"

    solution = result.best_solution

    # Query values
    assert solution.is_present(x), "x should be present"
    assert solution.is_present(y), "y should be present"

    x_start = solution.get_start(x)
    x_end = solution.get_end(x)
    y_start = solution.get_start(y)
    y_end = solution.get_end(y)

    print(f"  x: [{x_start}, {x_end})")
    print(f"  y: [{y_start}, {y_end})")

    # Check constraints are satisfied
    assert x_start >= 0, "x.start >= 0"
    assert x_end <= 100, "x.end <= 100"
    assert x_end - x_start == 10, "x.length == 10"
    assert y_end - y_start == 20, "y.length == 20"
    assert x_end <= y_start, "x ends before y starts"

    # Check objective
    assert solution.get_objective() == result.objective_value
    assert solution.get_objective() == y_end

    # Test get_value method
    x_value = solution.get_value(x)
    assert x_value is not None
    assert x_value == (x_start, x_end), "get_value should return (start, end) tuple"

    print("  ✓ Basic solution query passed")


def test_optional_variables():
    """Test optional variables and presence checking."""
    print("\nTest: Optional variables")

    model = cp.Model()

    # Create mandatory and optional interval variables (same length for alternative)
    x = model.interval_var(length=10, name="x")
    y = model.interval_var(length=10, name="y", optional=True)
    z = model.interval_var(length=10, name="z", optional=True)

    # Make constraint that allows y to be absent
    model.constraint(x.start() >= 0)
    model.constraint(x.end() <= 100)

    # Use alternative: either y or z must be equal to x
    model.alternative(x, [y, z])

    # Minimize makes x as early as possible
    model.minimize(x.end())

    # Solve
    result = cp.solve(model)

    assert result.best_solution is not None, "Expected a solution"
    solution = result.best_solution

    # x must be present (mandatory)
    assert solution.is_present(x), "x must be present"
    assert not solution.is_absent(x), "x must not be absent"

    # One of y or z must be present, one absent
    y_present = solution.is_present(y)
    z_present = solution.is_present(z)

    print(f"  x present: {solution.is_present(x)}")
    print(f"  y present: {y_present}")
    print(f"  z present: {z_present}")

    assert y_present != z_present, "Exactly one of y or z should be present"

    # Check that absent variable returns None
    if solution.is_absent(y):
        assert solution.get_start(y) is None, "Absent variable should return None"
        assert solution.get_end(y) is None, "Absent variable should return None"
        assert solution.get_value(y) is None, "Absent variable should return None"

    if solution.is_absent(z):
        assert solution.get_start(z) is None, "Absent variable should return None"
        assert solution.get_end(z) is None, "Absent variable should return None"
        assert solution.get_value(z) is None, "Absent variable should return None"

    # Check that present optional variable has valid values
    if solution.is_present(y):
        y_val = solution.get_value(y)
        assert y_val is not None
        assert solution.get_start(y) == solution.get_start(x)
        assert solution.get_end(y) == solution.get_end(x)

    print("  ✓ Optional variables test passed")


def test_int_and_bool_vars():
    """Test IntVar and BoolVar in solutions."""
    print("\nTest: IntVar and BoolVar")

    model = cp.Model()

    # Create interval and integer variables
    x = model.interval_var(length=10, name="x")
    count = model.int_var(min=0, max=100, name="count")

    # count = x.start
    model.constraint(count == x.start())

    # Constrain x
    model.constraint(x.start() >= 5)
    model.constraint(x.end() <= 50)

    # Solve
    result = cp.solve(model)

    assert result.best_solution is not None, "Expected a solution"
    solution = result.best_solution

    # Check IntVar value
    assert solution.is_present(count), "count should be present"
    count_val = solution.get_value(count)
    x_start = solution.get_start(x)

    print(f"  count: {count_val}")
    print(f"  x.start: {x_start}")

    assert count_val == x_start, "count should equal x.start"
    assert isinstance(count_val, int), "IntVar should return int"

    print("  ✓ IntVar test passed")


def test_manual_solution_construction():
    """Test creating a solution manually for warm start."""
    print("\nTest: Manual solution construction")

    model = cp.Model()

    x = model.interval_var(length=10, name="x")
    y = model.interval_var(length=20, name="y")

    # Create a solution manually
    solution = cp.Solution()

    # Set values
    solution.set_value(x, 0, 10)  # x at [0, 10)
    solution.set_value(y, 20, 40)  # y at [20, 40)
    solution.set_objective(40.0)

    # Query the values
    assert solution.is_present(x), "x should be present"
    assert solution.is_present(y), "y should be present"
    assert solution.get_start(x) == 0
    assert solution.get_end(x) == 10
    assert solution.get_start(y) == 20
    assert solution.get_end(y) == 40
    assert solution.get_objective() == 40.0

    # Test tuple unpacking
    x_start, x_end = solution.get_value(x)
    assert x_start == 0 and x_end == 10

    # Test setting absent
    z = model.interval_var(length=5, name="z", optional=True)
    solution.set_absent(z)
    assert solution.is_absent(z), "z should be absent"
    assert solution.get_value(z) is None

    print("  ✓ Manual solution construction passed")


def test_warm_start():
    """Test solving with a warm start."""
    print("\nTest: Warm start")

    model = cp.Model()

    x = model.interval_var(length=10, name="x")
    y = model.interval_var(length=20, name="y")

    # Add constraints
    x.end_before_start(y)
    model.constraint(x.start() >= 0)

    # Minimize completion time
    model.minimize(y.end())

    # Create a warm start solution (not optimal)
    warm_start = cp.Solution()
    warm_start.set_value(x, 10, 20)
    warm_start.set_value(y, 25, 45)
    warm_start.set_objective(45.0)

    print("  Solving with warm start...")
    result = cp.solve(model, warm_start=warm_start)

    assert result.best_solution is not None, "Expected a solution"
    solution = result.best_solution

    # The optimal solution should be better than warm start
    # (x at [0, 10), y at [10, 30), objective = 30)
    objective = solution.get_objective()
    print(f"  Optimal objective: {objective}")
    print(f"  Warm start objective: 45.0")

    assert objective <= 45.0, "Should find solution at least as good as warm start"

    # Check that the solution is actually optimal
    assert solution.get_start(x) == 0, "Optimal x should start at 0"
    assert solution.get_end(y) == 30, "Optimal y should end at 30"

    print("  ✓ Warm start test passed")

@pytest.mark.asyncio
async def test_solution_callback():
    """Test accessing solutions in on_solution callback."""
    print("\nTest: Solution callback")

    model = cp.Model()

    x = model.interval_var(length=10, name="x")
    y = model.interval_var(length=20, name="y")

    x.end_before_start(y)
    model.constraint(x.start() >= 0)
    model.minimize(y.end())

    # Track solutions in callback
    solutions_found = []

    def on_solution(event):
        print(f"  Solution found at {event['solveTime']:.3f}s")
        solution = event['solution']
        objective = solution.get_objective()
        print(f"    Objective: {objective}")

        # Verify solution object
        assert solution.is_present(x), "x should be present"
        assert solution.is_present(y), "y should be present"

        solutions_found.append(solution)

    solver = cp.Solver()
    solver.on_solution = on_solution
    solver.output_stream = None
    result = await solver.solve(model)

    print(f"  Total solutions found: {len(solutions_found)}")
    assert len(solutions_found) > 0, "Should have found at least one solution"
    assert result.best_solution is not None, "Should have best solution"

    # Last solution in callback should be the best solution
    # (They should have the same objective, but might not be the same object)
    assert solutions_found[-1].get_objective() == result.best_solution.get_objective()

    print("  ✓ Solution callback test passed")


def test_solutions_list():
    """Test that all solutions are stored in solutions list."""
    print("\nTest: Solutions list")

    model = cp.Model()

    x = model.interval_var(length=10, name="x")
    y = model.interval_var(length=20, name="y")

    x.end_before_start(y)
    model.constraint(x.start() >= 0)
    model.minimize(y.end())

    # Solve
    result = cp.solve(model)

    print(f"  Number of solutions: {result.nb_solutions}")
    print(f"  Solutions in list: {len(result.solutions)}")

    # Should have at least the best solution
    assert len(result.solutions) > 0, "Should have at least one solution in list"

    # Best solution should be in the list
    assert result.best_solution in result.solutions, "Best solution should be in solutions list"

    # All solutions should be valid
    for i, sol in enumerate(result.solutions):
        assert sol.is_present(x), f"Solution {i}: x should be present"
        assert sol.is_present(y), f"Solution {i}: y should be present"
        print(f"  Solution {i}: objective = {sol.get_objective()}")

    print("  ✓ Solutions list test passed")


def test_no_solution():
    """Test handling when no solution is found."""
    print("\nTest: No solution case")

    model = cp.Model()

    x = model.interval_var(length=10, name="x")
    y = model.interval_var(length=20, name="y")

    # Conflicting constraints - impossible to satisfy
    model.constraint(x.start() == 0)
    model.constraint(x.end() == 20)  # Conflicts with length=10

    result = cp.solve(model)

    print(f"  Solutions found: {result.nb_solutions}")
    assert result.nb_solutions == 0, "Should find no solution"
    assert result.best_solution is None, "Best solution should be None"
    assert len(result.solutions) == 0, "Solutions list should be empty"

    print("  ✓ No solution test passed")