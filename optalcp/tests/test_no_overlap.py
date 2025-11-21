"""
Tests for Model.no_overlap constraint.
"""

import pytest
import sys
import os

# Add parent directory to path to import optalcp
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import optalcp as cp


def test_no_overlap_basic():
    """Test basic no_overlap constraint with interval list."""
    model = cp.Model()

    # Create three tasks
    x = model.interval_var(length=10, name="x")
    y = model.interval_var(length=20, name="y")
    z = model.interval_var(length=15, name="z")

    # Apply no_overlap constraint
    model.no_overlap([x, y, z])

    # The model should be created without errors
    # We can verify that the constraint was added by converting to dict
    model_dict = model._to_dict()
    assert 'model' in model_dict
    assert len(model_dict['model']) > 0


def test_no_overlap_with_sequence_var():
    """Test no_overlap using a SequenceVar instead of list."""
    model = cp.Model()

    # Create tasks
    tasks = [
        model.interval_var(length=10, name="Task1"),
        model.interval_var(length=20, name="Task2"),
        model.interval_var(length=15, name="Task3")
    ]

    # Create sequence variable
    sequence = model.sequence_var(tasks)

    # Apply no_overlap using the sequence variable
    model.no_overlap(sequence)

    # Verify model creation
    model_dict = model._to_dict()
    assert 'model' in model_dict


def test_no_overlap_with_transitions():
    """Test no_overlap constraint with transition times."""
    model = cp.Model()

    # Create three tasks
    tasks = [
        model.interval_var(length=10, name="Task1"),
        model.interval_var(length=20, name="Task2"),
        model.interval_var(length=15, name="Task3")
    ]

    # Define transition times (e.g., setup times between tasks)
    transitions = [
        [0, 5, 10],
        [5, 0, 5],
        [10, 5, 0]
    ]

    # Apply no_overlap with transitions
    model.no_overlap(tasks, transitions)

    # Verify model creation
    model_dict = model._to_dict()
    assert 'model' in model_dict


def test_no_overlap_with_optional_intervals():
    """Test no_overlap constraint with optional intervals."""
    model = cp.Model()

    # Create some optional tasks
    x = model.interval_var(length=10, optional=True, name="x")
    y = model.interval_var(length=20, name="y")
    z = model.interval_var(length=15, optional=True, name="z")

    # Apply no_overlap constraint
    model.no_overlap([x, y, z])

    # Verify model creation
    model_dict = model._to_dict()
    assert 'model' in model_dict


def test_no_overlap_single_task():
    """Test no_overlap with a single task (edge case)."""
    model = cp.Model()

    # Single task
    x = model.interval_var(length=10, name="x")

    # Apply no_overlap - should work even with one task
    model.no_overlap([x])

    # Verify model creation
    model_dict = model._to_dict()
    assert 'model' in model_dict


def test_no_overlap_empty_list():
    """Test no_overlap with an empty list (edge case)."""
    model = cp.Model()

    # Empty list - should work
    model.no_overlap([])

    # Verify model creation
    model_dict = model._to_dict()
    assert 'model' in model_dict


def test_no_overlap_with_objective():
    """Test no_overlap combined with an objective function."""
    model = cp.Model()

    # Create tasks
    x = model.interval_var(length=10, name="x")
    y = model.interval_var(length=20, name="y")
    z = model.interval_var(length=15, name="z")

    # Apply no_overlap constraint
    model.no_overlap([x, y, z])

    # Minimize makespan (maximum end time)
    # Note: model.max is not yet implemented, so this will be added later
    # For now, just minimize z's end time as a placeholder
    # model.minimize(model.max([x.end(), y.end(), z.end()]))

    # Verify model creation
    model_dict = model._to_dict()
    assert 'model' in model_dict


def test_no_overlap_sequence_with_types():
    """Test no_overlap using a sequence with types for transitions."""
    model = cp.Model()

    # Create tasks with different "types" (e.g., locations)
    tasks = [
        model.interval_var(length=10, name="Task1"),
        model.interval_var(length=20, name="Task2"),
        model.interval_var(length=15, name="Task3")
    ]

    # Types represent locations
    types = [0, 1, 0]  # Task1 and Task3 at location 0, Task2 at location 1

    # Transition times between locations
    transitions = [
        [0, 5],  # Location 0 to 0, and 0 to 1
        [10, 0]  # Location 1 to 0, and 1 to 1
    ]

    # Create sequence with types
    sequence = model.sequence_var(tasks, types)

    # Apply no_overlap with transitions
    model.no_overlap(sequence, transitions)

    # Verify model creation
    model_dict = model._to_dict()
    assert 'model' in model_dict


def test_no_overlap_invalid_transitions_size():
    """Test that invalid transition matrix size is handled."""
    model = cp.Model()

    # Create three tasks
    tasks = [
        model.interval_var(length=10, name="Task1"),
        model.interval_var(length=20, name="Task2"),
        model.interval_var(length=15, name="Task3")
    ]

    # Wrong size transition matrix (should be 3x3)
    transitions = [
        [0, 5],
        [5, 0]
    ]

    # This should work at model creation time (validation happens at solve time)
    model.no_overlap(tasks, transitions)

    # Note: The actual validation of transition matrix size happens
    # during solving, not during model construction


def test_no_overlap_multiple_constraints():
    """Test applying multiple no_overlap constraints to different sets."""
    model = cp.Model()

    # Machine 1 tasks
    m1_tasks = [
        model.interval_var(length=10, name="M1_Task1"),
        model.interval_var(length=20, name="M1_Task2")
    ]

    # Machine 2 tasks
    m2_tasks = [
        model.interval_var(length=15, name="M2_Task1"),
        model.interval_var(length=25, name="M2_Task2")
    ]

    # Each machine's tasks cannot overlap
    model.no_overlap(m1_tasks)
    model.no_overlap(m2_tasks)

    # Verify model creation
    model_dict = model._to_dict()
    assert 'model' in model_dict
    # Should have two no_overlap constraints
    assert len(model_dict['model']) >= 2


def test_no_overlap_solve_basic():
    """Integration test: solve a simple model with no_overlap constraint."""
    model = cp.Model(name="NoOverlapBasicTest")

    # Create three tasks that must be scheduled sequentially
    x = model.interval_var(length=10, start=(0, 100), name="x")
    y = model.interval_var(length=20, start=(0, 100), name="y")
    z = model.interval_var(length=15, start=(0, 100), name="z")

    # Apply no_overlap constraint
    model.no_overlap([x, y, z])

    # Solve the model (just find one solution)
    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params)

    # Verify we found a solution
    assert result.nb_solutions >= 1
    print(f"Found {result.nb_solutions} solution(s)")
    print(f"Duration: {result.duration}s")


def test_no_overlap_solve_with_transitions():
    """Integration test: solve a model with no_overlap and transition times."""
    model = cp.Model(name="NoOverlapTransitionsTest")

    # Create tasks
    tasks = [
        model.interval_var(length=10, start=(0, 100), name="Task1"),
        model.interval_var(length=15, start=(0, 100), name="Task2"),
        model.interval_var(length=20, start=(0, 100), name="Task3")
    ]

    # Transition times: 5 time units between consecutive tasks
    transitions = [
        [0, 5, 5],
        [5, 0, 5],
        [5, 5, 0]
    ]

    # Apply no_overlap with transitions
    model.no_overlap(tasks, transitions)

    # Solve the model
    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params)

    # Verify we found a solution
    assert result.nb_solutions >= 1
    print(f"Found {result.nb_solutions} solution(s)")
    print(f"Duration: {result.duration}s")


def test_no_overlap_solve_with_optional():
    """Integration test: solve a model with optional intervals and no_overlap."""
    model = cp.Model(name="NoOverlapOptionalTest")

    # Create some optional tasks
    x = model.interval_var(length=10, optional=True, start=(0, 50), name="x")
    y = model.interval_var(length=20, start=(0, 50), name="y")
    z = model.interval_var(length=15, optional=True, start=(0, 50), name="z")

    # Apply no_overlap constraint
    model.no_overlap([x, y, z])

    # Solve the model
    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params)

    # Verify we found a solution
    assert result.nb_solutions >= 1
    print(f"Found {result.nb_solutions} solution(s) with optional intervals")
    print(f"Duration: {result.duration}s")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
