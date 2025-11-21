"""
Tests for SequenceVar class.
"""

import pytest
import optalcp as cp


def test_sequence_var_creation():
    """Test creating a sequence variable."""

    model = cp.Model()

    # Create some interval variables
    x = model.interval_var(length=10, name="x")
    y = model.interval_var(length=10, name="y")
    z = model.interval_var(length=10, name="z")

    # Create a sequence variable
    seq = model.sequence_var([x, y, z])

    # Verify it's the right type
    assert isinstance(seq, cp.SequenceVar)


def test_sequence_var_with_types():
    """Test creating a sequence variable with explicit types."""

    model = cp.Model()

    # Create interval variables
    tasks = [
        model.interval_var(length=10, name=f"task{i}")
        for i in range(5)
    ]

    # Create sequence with types (e.g., locations)
    types = [0, 0, 1, 1, 2]
    seq = model.sequence_var(tasks, types)

    assert isinstance(seq, cp.SequenceVar)


def test_sequence_var_no_overlap():
    """Test no_overlap constraint without transitions."""

    model = cp.Model()

    # Create interval variables
    x = model.interval_var(length=10, name="x")
    y = model.interval_var(length=10, name="y")
    z = model.interval_var(length=10, name="z")

    # Create sequence and add no_overlap constraint
    seq = model.sequence_var([x, y, z])
    seq.no_overlap()

    # Should be able to serialize the model
    model_dict = model._to_dict()
    assert 'model' in model_dict


def test_sequence_var_no_overlap_with_transitions():
    """Test no_overlap constraint with transition matrix."""

    model = cp.Model()

    # Create interval variables for tasks at different locations
    tasks = [
        model.interval_var(length=20, start=(0, None), end=(None, 100), name="Task0"),
        model.interval_var(length=40, start=(70, None), end=(None, 200), name="Task1"),
        model.interval_var(length=10, start=(0, None), end=(None, 200), name="Task2"),
    ]

    # Types represent locations
    types = [0, 0, 1]

    # Transition matrix: travel times between locations
    transitions = [
        [0, 10],   # From location 0 to 0 or 1
        [15, 0]    # From location 1 to 0 or 1
    ]

    # Create sequence with no_overlap and transitions
    seq = model.sequence_var(tasks, types)
    seq.no_overlap(transitions)

    # Should be able to serialize the model
    model_dict = model._to_dict()
    assert 'model' in model_dict


def test_sequence_var_transitions_validation():
    """Test that transitions parameter is validated."""

    model = cp.Model()

    x = model.interval_var(length=10, name="x")
    y = model.interval_var(length=10, name="y")

    seq = model.sequence_var([x, y])

    # Test invalid transition types
    with pytest.raises(TypeError):
        seq.no_overlap("not a list")

    with pytest.raises(TypeError):
        seq.no_overlap([1, 2, 3])  # Not a 2D list

    with pytest.raises(TypeError):
        seq.no_overlap([[1, 2], ["a", "b"]])  # Not all integers


def test_sequence_var_example():
    """Test the full example from the docstring."""

    # Travel times between locations
    transitions = [
        [0, 10, 10],
        [15, 0, 10],
        [5, 5, 0]
    ]

    # Tasks to be scheduled
    tasks_data = [
        {"location": 0, "length": 20, "start_min": 0, "end_max": 100},
        {"location": 0, "length": 40, "start_min": 70, "end_max": 200},
        {"location": 1, "length": 10, "start_min": 0, "end_max": 200},
        {"location": 1, "length": 30, "start_min": 100, "end_max": 200},
        {"location": 1, "length": 10, "start_min": 0, "end_max": 150},
        {"location": 2, "length": 15, "start_min": 50, "end_max": 250},
        {"location": 2, "length": 10, "start_min": 20, "end_max": 60},
        {"location": 2, "length": 20, "start_min": 110, "end_max": 250},
    ]

    model = cp.Model()

    # Create interval variables from tasks
    task_vars = [
        model.interval_var(
            name=f"Task{i}",
            length=t["length"],
            start=(t["start_min"], None),
            end=(None, t["end_max"])
        )
        for i, t in enumerate(tasks_data)
    ]

    # Create array of locations (types)
    types = [t["location"] for t in tasks_data]

    # Create the sequence variable for the tasks
    sequence = model.sequence_var(task_vars, types)

    # Tasks must not overlap and transitions must be respected
    sequence.no_overlap(transitions)

    # Should be able to serialize the model
    model_dict = model._to_dict()
    assert 'model' in model_dict
    assert len(model_dict['model']) > 0


def test_sequence_var_with_optional_intervals():
    """Test sequence variable with optional intervals."""

    model = cp.Model()

    # Create mix of required and optional interval variables
    x = model.interval_var(length=10, name="x")
    y = model.interval_var(length=10, optional=True, name="y")
    z = model.interval_var(length=10, optional=True, name="z")

    # Create sequence - optional intervals can be absent
    seq = model.sequence_var([x, y, z])
    seq.no_overlap()

    # Should be able to serialize the model
    model_dict = model._to_dict()
    assert 'model' in model_dict
