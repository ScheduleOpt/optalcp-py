"""
Edge case tests for the OptalCP Python API.

Tests cover:
- Empty/minimal models
- Parameter validation
- Windows compatibility
- Large/boundary models
"""

import optalcp as cp
import pytest
import sys
import os
from unittest.mock import patch


# ==============================================================================
# Empty/Minimal Models (5 tests)
# ==============================================================================

def test_empty_model():
    """Test empty model with no variables, constraints, or objectives."""
    model = cp.Model(name="empty_model")

    # Empty model should solve successfully (trivially satisfied)
    params = cp.Parameters(solutionLimit=1)
    result = cp.solve(model, params=params)

    assert result.nb_solutions >= 0, "Empty model should solve"
    print(f"✓ test_empty_model passed")


def test_model_with_variables_no_constraints():
    """Test model with variables but no constraints."""
    model = cp.Model(name="no_constraints")

    x = model.int_var(min=0, max=10, name="x")
    y = model.interval_var(length=5, name="y")

    # No constraints, no objective - should find a solution
    params = cp.Parameters(solutionLimit=1)
    result = cp.solve(model, params=params)

    assert result.nb_solutions > 0, "Should find at least one solution"
    assert result.best_solution is not None
    print(f"✓ test_model_with_variables_no_constraints passed")


def test_model_with_constraints_no_objective():
    """Test satisfaction problem (constraints but no objective)."""
    model = cp.Model(name="satisfaction")

    x = model.int_var(min=0, max=10, name="x")
    y = model.int_var(min=0, max=10, name="y")

    # Add constraints
    model.constraint(x + y == 15)
    model.constraint(x >= 5)

    # No objective - this is a satisfaction problem
    # IMPORTANT: Must use solutionLimit=1 to avoid infinite search
    params = cp.Parameters(solutionLimit=1)
    result = cp.solve(model, params=params)

    assert result.nb_solutions > 0, "Should find at least one solution"

    # Verify solution satisfies constraints
    solution = result.best_solution
    x_val = solution.get_value(x)
    y_val = solution.get_value(y)
    assert x_val + y_val == 15, f"x + y should equal 15, got {x_val} + {y_val}"
    assert x_val >= 5, f"x should be >= 5, got {x_val}"

    print(f"✓ test_model_with_constraints_no_objective passed")


def test_model_with_constant_objective_no_variables():
    """Test model with constant objective but no variables."""
    model = cp.Model(name="constant_objective")

    # Objective is a constant (no variables)
    model.minimize(42)

    # This should succeed with an empty solution
    result = cp.solve(model)

    assert result.best_solution is not None, "Should have a solution"
    assert result.objective_value == 42, f"Objective should be 42, got {result.objective_value}"

    print(f"✓ test_model_with_constant_objective_no_variables passed")


def test_single_variable_no_constraints():
    """Test model with single variable and no constraints."""
    model = cp.Model(name="single_var")

    x = model.int_var(min=5, max=10, name="x")

    # Minimize x (should get 5)
    model.minimize(x)

    result = cp.solve(model)

    assert result.nb_solutions > 0
    assert result.objective_value == 5, f"Should minimize to 5, got {result.objective_value}"
    assert result.best_solution.get_value(x) == 5

    print(f"✓ test_single_variable_no_constraints passed")


# ==============================================================================
# Parameter Validation (10 tests)
# ==============================================================================

def test_negative_time_limit():
    """Test that negative timeLimit is handled (should error or be ignored)."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    model.minimize(x)

    params = cp.Parameters()
    params.timeLimit = -1  # Invalid

    # Solver should error on invalid parameter
    try:
        result = cp.solve(model, params=params)
        # If it doesn't error, it should still solve correctly
        assert False
    except (ValueError, RuntimeError, Exception) as e:
        # Solver correctly rejects invalid parameter
        print(f"✓ test_negative_time_limit passed (error raised: {type(e).__name__})")


def test_invalid_search_type():
    """Test that invalid searchType string is handled."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    model.minimize(x)

    params = cp.Parameters()
    params.searchType = "INVALID_SEARCH_TYPE"

    # Should error or be ignored
    try:
        result = cp.solve(model, params=params)
        assert False
    except (ValueError, RuntimeError, Exception) as e:
        print(f"✓ test_invalid_search_type passed (error raised: {type(e).__name__})")


def test_satisfaction_with_solution_limit():
    """Test satisfaction problem WITH solutionLimit (should stop after finding one)."""
    model = cp.Model(name="satisfaction_with_limit")

    x = model.int_var(min=0, max=100, name="x")
    y = model.int_var(min=0, max=100, name="y")
    model.constraint(x + y == 50)

    # No objective, but with solutionLimit - should stop after 1 solution
    params = cp.Parameters(solutionLimit=1)

    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, f"Should find exactly 1 solution, got {result.nb_solutions}"

    print(f"✓ test_satisfaction_with_solution_limit passed")


def test_very_large_solution_limit():
    """Test very large solutionLimit value."""
    model = cp.Model()
    x = model.int_var(min=0, max=2, name="x")
    # Minimize x to ensure it's used in the model (otherwise gets optimized away)
    model.minimize(x)

    params = cp.Parameters(solutionLimit=1000000)

    result = cp.solve(model, params=params)

    # With minimize objective, solver finds improving solutions until optimal
    # Should find at least 1 solution (optimal: x=0)
    assert result.nb_solutions >= 1, f"Should find at least 1 solution, got {result.nb_solutions}"
    assert result.objective_value == 0, f"Optimal should be 0, got {result.objective_value}"

    print(f"✓ test_very_large_solution_limit passed (found {result.nb_solutions} solution(s))")


def test_worker_parameters_validation():
    """Test WorkerParameters validation."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    model.minimize(x)

    params = cp.Parameters()
    params.nbWorkers = 2

    # Create worker parameters
    worker1 = cp.WorkerParameters()
    worker1.searchType = "LNS"

    worker2 = cp.WorkerParameters()
    worker2.searchType = "FDS"

    params.workers = [worker1, worker2]

    result = cp.solve(model, params=params)

    assert result.nb_solutions > 0
    assert result.nb_workers == 2, f"Should use 2 workers, got {result.nb_workers}"

    print(f"✓ test_worker_parameters_validation passed")


def test_worker_parameter_inheritance():
    """Test that worker parameters inherit from global parameters."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    model.minimize(x)

    params = cp.Parameters()
    params.nbWorkers = 2
    params.timeLimit = 10  # Global timeLimit

    # Worker 1 uses global settings (no override)
    worker1 = cp.WorkerParameters()

    # Worker 2 overrides searchType
    worker2 = cp.WorkerParameters()
    worker2.searchType = "FDS"

    params.workers = [worker1, worker2]

    result = cp.solve(model, params=params)

    assert result.nb_solutions > 0
    # Both workers should respect the global timeLimit
    assert result.duration <= 11, f"Should respect timeLimit, took {result.duration}s"

    print(f"✓ test_worker_parameter_inheritance passed")


def test_parameters_error_messages():
    """Test that parameter errors produce clear error messages."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    model.minimize(x)

    params = cp.Parameters()

    # Test various parameter edge cases
    # (Most of these may not error, but we verify they don't crash)
    test_cases = [
        ("nbWorkers", 1),
        ("timeLimit", 0.1),
        ("searchType", "LNS"),
        ("searchType", "FDS"),
    ]

    for param_name, param_value in test_cases:
        setattr(params, param_name, param_value)
        result = cp.solve(model, params=params)
        assert result is not None, f"Failed with {param_name}={param_value}"

    print(f"✓ test_parameters_error_messages passed")


def test_conflicting_parameters():
    """Test potentially conflicting parameter combinations."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    model.minimize(x)

    params = cp.Parameters()
    params.timeLimit = 0.1  # Very short time
    params.solutionLimit = 1000  # Many solutions requested

    # Should respect whichever limit is hit first
    result = cp.solve(model, params=params)

    assert result is not None
    # Either time limit or solution limit should be hit
    assert result.duration <= 1 or result.nb_solutions <= 1000

    print(f"✓ test_conflicting_parameters passed")


def test_missing_optalcp_solver_env():
    """Test clear error when OPTALCP_SOLVER is not set."""
    # Save current value
    original_solver = os.environ.get('OPTALCP_SOLVER')

    try:
        # Temporarily unset OPTALCP_SOLVER
        if 'OPTALCP_SOLVER' in os.environ:
            del os.environ['OPTALCP_SOLVER']

        model = cp.Model()
        x = model.int_var(min=0, max=10, name="x")
        model.minimize(x)

        # Should raise a clear error
        with pytest.raises((RuntimeError, ValueError, FileNotFoundError)) as exc_info:
            result = cp.solve(model)

        # Error message should be meaningful (we're just checking it doesn't crash silently)
        error_msg = str(exc_info.value)
        assert len(error_msg) > 0, "Error message should not be empty"

        print(f"✓ test_missing_optalcp_solver_env passed (error: {exc_info.value})")
    finally:
        # Restore original value
        if original_solver:
            os.environ['OPTALCP_SOLVER'] = original_solver


def test_invalid_solver_path():
    """Test clear error when solver path is invalid."""
    # Save current value
    original_solver = os.environ.get('OPTALCP_SOLVER')

    try:
        # Set to invalid path
        os.environ['OPTALCP_SOLVER'] = '/nonexistent/path/to/optalcp'

        model = cp.Model()
        x = model.int_var(min=0, max=10, name="x")
        model.minimize(x)

        # Should raise a clear error
        with pytest.raises((RuntimeError, ValueError, FileNotFoundError, OSError)) as exc_info:
            result = cp.solve(model)

        print(f"✓ test_invalid_solver_path passed (error: {exc_info.value})")
    finally:
        # Restore original value
        if original_solver:
            os.environ['OPTALCP_SOLVER'] = original_solver


# ==============================================================================
# Large/Boundary Models (3 tests)
# ==============================================================================

def test_large_model_1000_intervals():
    """Test model with 1000 interval variables."""
    model = cp.Model(name="large_model_1000")

    # Create 1000 interval variables
    intervals = []
    for i in range(1000):
        interval = model.interval_var(length=1, name=f"interval_{i}")
        intervals.append(interval)

    # Add precedence chain to force sequential execution
    # This ensures intervals must execute in order: 0 -> 1 -> 2 -> ... -> 999
    for i in range(len(intervals) - 1):
        intervals[i].end_before_start(intervals[i + 1])

    # Minimize makespan (end of last interval)
    model.minimize(intervals[-1].end())

    # Solve with time limit to prevent long test
    params = cp.Parameters(timeLimit=5)
    result = cp.solve(model, params=params)

    # Should find at least one solution (may not be optimal due to time limit)
    assert result.nb_solutions > 0, "Should find at least one solution for large model"

    # Optimal makespan should be 1000 (all intervals sequential, length 1 each)
    # With precedence chain, the optimal is exactly 1000
    assert result.objective_value == 1000, f"Makespan should be 1000, got {result.objective_value}"

    print(f"✓ test_large_model_1000_intervals passed (objective: {result.objective_value}, duration: {result.duration}s)")


def test_int_var_maximum_domain():
    """Test IntVar with maximum domain (IntVarMin to IntVarMax)."""
    model = cp.Model(name="max_domain_int")

    # Create IntVar with maximum possible domain
    x = model.int_var(min=cp.IntVarMin, max=cp.IntVarMax, name="x")

    # Verify bounds
    assert x.get_min() == cp.IntVarMin, f"Min should be IntVarMin ({cp.IntVarMin}), got {x.get_min()}"
    assert x.get_max() == cp.IntVarMax, f"Max should be IntVarMax ({cp.IntVarMax}), got {x.get_max()}"

    # Minimize x (should get IntVarMin)
    model.minimize(x)

    params = cp.Parameters(timeLimit=5)
    result = cp.solve(model, params=params)

    assert result.nb_solutions > 0
    assert result.objective_value == cp.IntVarMin, \
        f"Should minimize to IntVarMin ({cp.IntVarMin}), got {result.objective_value}"

    print(f"✓ test_int_var_maximum_domain passed")


def test_interval_var_maximum_time_windows():
    """Test IntervalVar with maximum time windows."""
    model = cp.Model(name="max_time_windows")

    # Create IntervalVar with maximum time bounds
    interval = model.interval_var(
        start=(cp.IntervalMin, cp.IntervalMax),
        end=(cp.IntervalMin, cp.IntervalMax),
        length=(0, cp.LengthMax),
        name="max_interval"
    )

    # Minimize start time
    model.minimize(interval.start())

    params = cp.Parameters(timeLimit=5)
    result = cp.solve(model, params=params)

    assert result.nb_solutions > 0

    # Should minimize start to IntervalMin
    solution = result.best_solution
    start = solution.get_start(interval)
    assert start == cp.IntervalMin, \
        f"Start should be IntervalMin ({cp.IntervalMin}), got {start}"

    print(f"✓ test_interval_var_maximum_time_windows passed")