"""
Tests for IntVar class member functions.
"""

import optalcp as cp
from optalcp import IntVarMin, IntVarMax


def test_int_var_presence_queries():
    """Test presence status query methods."""
    model = cp.Model()

    # Present int var (default)
    x = model.int_var(min=0, max=10, name="x")
    assert x.is_present()
    assert not x.is_optional()
    assert not x.is_absent()


def test_int_var_domain_getters():
    """Test domain getter methods."""
    model = cp.Model()

    # Int var with specified domain
    x = model.int_var(min=5, max=15, name="x")
    assert x.get_min() == 5
    assert x.get_max() == 15

    # Int var with default domain
    y = model.int_var(name="y")
    assert y.get_min() == IntVarMin
    assert y.get_max() == IntVarMax


def test_int_var_absent_getters():
    """Test that getters return None for absent variables."""
    model = cp.Model()

    x = model.int_var(min=0, max=10, name="x")
    x.make_absent()

    assert x.is_absent()
    assert x.get_min() is None
    assert x.get_max() is None


def test_int_var_make_methods():
    """Test make_optional(), make_present(), make_absent()."""
    model = cp.Model()

    # Start with present variable
    x = model.int_var(min=0, max=10, name="x")
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


def test_int_var_set_min_max():
    """Test set_min() and set_max()."""
    model = cp.Model()
    x = model.int_var(name="x")

    # Set min
    x.set_min(10)
    assert x.get_min() == 10
    assert x.get_max() == IntVarMax  # Max unchanged

    # Set max
    x.set_max(100)
    assert x.get_min() == 10  # Min unchanged
    assert x.get_max() == 100


def test_int_var_set_range():
    """Test set_range()."""
    model = cp.Model()
    x = model.int_var(name="x")

    # Set range
    x.set_range(5, 50)
    assert x.get_min() == 5
    assert x.get_max() == 50


def test_int_var_multiple_calls():
    """Test that methods can be called multiple times."""
    model = cp.Model()

    x = model.int_var(name="x")

    # Multiple calls (not chained)
    x.set_min(0)
    x.set_max(100)
    x.make_optional()

    assert x.get_min() == 0
    assert x.get_max() == 100
    assert x.is_optional()

    # Multiple calls with set_range
    x.make_present()
    x.set_range(10, 50)
    assert x.is_present()
    assert x.get_min() == 10
    assert x.get_max() == 50


def test_int_var_arithmetic_operations():
    """Test that arithmetic operations still work."""
    model = cp.Model()

    x = model.int_var(min=0, max=10, name="x")
    y = model.int_var(min=0, max=10, name="y")

    # Arithmetic operations should still work
    sum_expr = x + y
    diff_expr = x - y
    prod_expr = x * y
    neg_expr = -x

    # Create constraints
    model.constraint(sum_expr <= 15)
    model.constraint(diff_expr >= -5)


def test_int_var_comparison_operations():
    """Test that comparison operations still work."""
    model = cp.Model()

    x = model.int_var(min=0, max=10, name="x")
    y = model.int_var(min=0, max=10, name="y")

    # Comparison operations should still work
    model.constraint(x <= y)
    model.constraint(x >= 0)
    model.constraint(x == y + 1)
    model.constraint(x != y)


def test_int_var_with_solver():
    """Test that modified int variables work with the solver."""
    model = cp.Model()

    x = model.int_var(name="x")
    x.set_range(0, 100)

    y = model.int_var(name="y")
    y.set_range(0, 100)

    model.constraint(x + y == 50)
    model.constraint(x >= 20)
    model.minimize(x)

    result = cp.solve(model)
    assert result.nb_solutions > 0
