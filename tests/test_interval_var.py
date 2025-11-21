"""
Tests for IntervalVar class member functions.
"""

import optalcp as cp
from optalcp import IntervalMin, IntervalMax, LengthMax


def test_interval_var_presence_queries():
    """Test presence status query methods."""
    model = cp.Model()

    # Present interval (default)
    x = model.interval_var(length=10, name="x")
    assert x.is_present()
    assert not x.is_optional()
    assert not x.is_absent()

    # Optional interval
    y = model.interval_var(length=10, optional=True, name="y")
    assert y.is_optional()
    assert not y.is_present()
    assert not y.is_absent()


def test_interval_var_domain_getters():
    """Test domain getter methods."""
    model = cp.Model()

    # Interval with specified domains
    x = model.interval_var(
        start=(10, 100),
        end=(20, 200),
        length=(5, 50),
        name="x"
    )

    assert x.get_start_min() == 10
    assert x.get_start_max() == 100
    assert x.get_end_min() == 20
    assert x.get_end_max() == 200
    assert x.get_length_min() == 5
    assert x.get_length_max() == 50

    # Interval with default domains
    y = model.interval_var(name="y")
    assert y.get_start_min() == IntervalMin
    assert y.get_start_max() == IntervalMax
    assert y.get_end_min() == IntervalMin
    assert y.get_end_max() == IntervalMax
    assert y.get_length_min() == 0
    assert y.get_length_max() == LengthMax


def test_interval_var_absent_getters():
    """Test that getters return None for absent intervals."""
    model = cp.Model()

    x = model.interval_var(length=10, name="x")
    x.make_absent()

    assert x.get_start_min() is None
    assert x.get_start_max() is None
    assert x.get_end_min() is None
    assert x.get_end_max() is None
    assert x.get_length_min() is None
    assert x.get_length_max() is None


def test_interval_var_make_methods():
    """Test make_optional(), make_present(), make_absent()."""
    model = cp.Model()

    # Start with present interval
    x = model.interval_var(length=10, name="x")
    assert x.is_present()

    # Make it optional
    x.make_optional()
    assert x.is_optional()
    assert not x.is_present()
    assert not x.is_absent()

    # Make it absent
    x.make_absent()
    assert x.is_absent()
    assert not x.is_optional()
    assert not x.is_present()

    # Make it present again
    x.make_present()
    assert x.is_present()
    assert not x.is_optional()
    assert not x.is_absent()


def test_interval_var_set_start():
    """Test set_start(), set_start_min(), set_start_max()."""
    model = cp.Model()
    x = model.interval_var(name="x")

    # Set to exact value
    x.set_start(50)
    assert x.get_start_min() == 50
    assert x.get_start_max() == 50

    # Set range
    x.set_start(10, 100)
    assert x.get_start_min() == 10
    assert x.get_start_max() == 100

    # Set min only
    x.set_start_min(20)
    assert x.get_start_min() == 20
    assert x.get_start_max() == 100  # Max unchanged

    # Set max only
    x.set_start_max(90)
    assert x.get_start_min() == 20  # Min unchanged
    assert x.get_start_max() == 90


def test_interval_var_set_end():
    """Test set_end(), set_end_min(), set_end_max()."""
    model = cp.Model()
    x = model.interval_var(name="x")

    # Set to exact value
    x.set_end(100)
    assert x.get_end_min() == 100
    assert x.get_end_max() == 100

    # Set range
    x.set_end(50, 150)
    assert x.get_end_min() == 50
    assert x.get_end_max() == 150

    # Set min only
    x.set_end_min(60)
    assert x.get_end_min() == 60
    assert x.get_end_max() == 150  # Max unchanged

    # Set max only
    x.set_end_max(140)
    assert x.get_end_min() == 60  # Min unchanged
    assert x.get_end_max() == 140


def test_interval_var_set_length():
    """Test set_length(), set_length_min(), set_length_max()."""
    model = cp.Model()
    x = model.interval_var(name="x")

    # Set to exact value
    x.set_length(10)
    assert x.get_length_min() == 10
    assert x.get_length_max() == 10

    # Set range
    x.set_length(5, 20)
    assert x.get_length_min() == 5
    assert x.get_length_max() == 20

    # Set min only
    x.set_length_min(8)
    assert x.get_length_min() == 8
    assert x.get_length_max() == 20  # Max unchanged

    # Set max only
    x.set_length_max(15)
    assert x.get_length_min() == 8  # Min unchanged
    assert x.get_length_max() == 15


def test_interval_var_multiple_calls():
    """Test that methods can be called multiple times."""
    model = cp.Model()

    x = model.interval_var(name="x")

    # Multiple calls (not chained)
    x.set_start(0, 100)
    x.set_end(10, 110)
    x.set_length(10)
    x.make_optional()

    assert x.get_start_min() == 0
    assert x.get_start_max() == 100
    assert x.get_end_min() == 10
    assert x.get_end_max() == 110
    assert x.get_length_min() == 10
    assert x.get_length_max() == 10
    assert x.is_optional()


def test_interval_var_expression_methods():
    """Test that expression methods still work."""
    model = cp.Model()

    x = model.interval_var(length=10, name="x")
    y = model.interval_var(length=10, name="y")

    # These methods should still work
    start_expr = x.start()
    end_expr = x.end()
    length_expr = x.length()
    presence_expr = x.presence()

    # Create constraints using expressions
    model.constraint(start_expr >= 0)
    model.constraint(end_expr <= 100)

    # Precedence constraints
    x.end_before_start(y)
    x.end_at_start(y, delay=5)


def test_interval_var_with_solver():
    """Test that modified interval variables work with the solver."""
    model = cp.Model()

    x = model.interval_var(name="x")
    x.set_start(0, 50)
    x.set_length(10)

    y = model.interval_var(name="y")
    y.set_start(20, 100)
    y.set_length(10)

    x.end_before_start(y)
    model.minimize(y.end())

    result = cp.solve(model)
    assert result.nb_solutions > 0
