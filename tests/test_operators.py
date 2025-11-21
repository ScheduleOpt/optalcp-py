#!/usr/bin/env python3
"""
Comprehensive tests for IntExpr and BoolExpr operators.

Tests cover all operator overloads with different argument types.
Each test creates a solvable model and verifies a solution exists.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import optalcp as cp


def test_intexpr_add_intexpr():
    """Test IntExpr + IntExpr."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    y = model.int_var(min=0, max=10, name="y")
    z = x + y
    model.constraint(z <= 15)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    y_val = sol.get_value(y)
    assert y_val is not None
    assert x_val + y_val <= 15, f"Expected {x_val} + {y_val} <= 15"


def test_intexpr_add_int():
    """Test IntExpr + int."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    z = x + 5
    model.constraint(z <= 12)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val + 5 <= 12, f"Expected {x_val} + 5 <= 12"


def test_intexpr_add_bool():
    """Test IntExpr + bool."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    z = x + True  # True is treated as 1
    model.constraint(z <= 11)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val + 1 <= 11, f"Expected {x_val} + 1 <= 11"


def test_intexpr_radd_int():
    """Test int + IntExpr (reverse add)."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    z = 5 + x
    model.constraint(z <= 12)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert 5 + x_val <= 12, f"Expected 5 + {x_val} <= 12"


def test_intexpr_radd_bool():
    """Test bool + IntExpr (reverse add)."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    z = True + x  # True is treated as 1
    model.constraint(z <= 11)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert 1 + x_val <= 11, f"Expected 1 + {x_val} <= 11"


def test_intexpr_sub_intexpr():
    """Test IntExpr - IntExpr."""
    model = cp.Model()
    x = model.int_var(min=5, max=10, name="x")
    y = model.int_var(min=0, max=3, name="y")
    z = x - y
    model.constraint(z >= 2)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    y_val = sol.get_value(y)
    assert y_val is not None
    assert x_val - y_val >= 2, f"Expected {x_val} - {y_val} >= 2"


def test_intexpr_sub_int():
    """Test IntExpr - int."""
    model = cp.Model()
    x = model.int_var(min=5, max=10, name="x")
    z = x - 3
    model.constraint(z >= 2)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val - 3 >= 2, f"Expected {x_val} - 3 >= 2"


def test_intexpr_sub_bool():
    """Test IntExpr - bool."""
    model = cp.Model()
    x = model.int_var(min=2, max=10, name="x")
    z = x - True  # True is treated as 1
    model.constraint(z >= 1)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val - 1 >= 1, f"Expected {x_val} - 1 >= 1"


def test_intexpr_rsub_int():
    """Test int - IntExpr (reverse subtract)."""
    model = cp.Model()
    x = model.int_var(min=0, max=5, name="x")
    z = 10 - x
    model.constraint(z >= 5)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert 10 - x_val >= 5, f"Expected 10 - {x_val} >= 5"


def test_intexpr_rsub_bool():
    """Test bool - IntExpr (reverse subtract)."""
    model = cp.Model()
    x = model.int_var(min=0, max=1, name="x")
    z = True - x  # True is treated as 1
    model.constraint(z >= 0)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert 1 - x_val >= 0, f"Expected 1 - {x_val} >= 0"


def test_intexpr_mul_intexpr():
    """Test IntExpr * IntExpr."""
    model = cp.Model()
    x = model.int_var(min=1, max=5, name="x")
    y = model.int_var(min=1, max=3, name="y")
    z = x * y
    model.constraint(z <= 10)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    y_val = sol.get_value(y)
    assert y_val is not None
    assert x_val * y_val <= 10, f"Expected {x_val} * {y_val} <= 10"


def test_intexpr_mul_int():
    """Test IntExpr * int."""
    model = cp.Model()
    x = model.int_var(min=1, max=5, name="x")
    z = x * 3
    model.constraint(z <= 12)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val * 3 <= 12, f"Expected {x_val} * 3 <= 12"


def test_intexpr_mul_bool():
    """Test IntExpr * bool."""
    model = cp.Model()
    x = model.int_var(min=1, max=10, name="x")
    z = x * True  # True is treated as 1
    model.constraint(z <= 10)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val * 1 <= 10, f"Expected {x_val} * 1 <= 10"


def test_intexpr_rmul_int():
    """Test int * IntExpr (reverse multiply)."""
    model = cp.Model()
    x = model.int_var(min=1, max=5, name="x")
    z = 3 * x
    model.constraint(z <= 12)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert 3 * x_val <= 12, f"Expected 3 * {x_val} <= 12"


def test_intexpr_rmul_bool():
    """Test bool * IntExpr (reverse multiply)."""
    model = cp.Model()
    x = model.int_var(min=1, max=10, name="x")
    z = True * x  # True is treated as 1
    model.constraint(z <= 10)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert 1 * x_val <= 10, f"Expected 1 * {x_val} <= 10"


def test_intexpr_floordiv_intexpr():
    """Test IntExpr // IntExpr (floor division)."""
    model = cp.Model()
    x = model.int_var(min=10, max=20, name="x")
    y = model.int_var(min=2, max=5, name="y")
    z = x // y
    model.constraint(z >= 2)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    y_val = sol.get_value(y)
    assert y_val is not None
    assert x_val // y_val >= 2, f"Expected {x_val} // {y_val} >= 2"


def test_intexpr_floordiv_int():
    """Test IntExpr // int."""
    model = cp.Model()
    x = model.int_var(min=10, max=20, name="x")
    z = x // 3
    model.constraint(z >= 3)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val // 3 >= 3, f"Expected {x_val} // 3 >= 3"


def test_intexpr_floordiv_bool():
    """Test IntExpr // bool."""
    model = cp.Model()
    x = model.int_var(min=5, max=10, name="x")
    z = x // True  # True is treated as 1, so z = x
    model.constraint(z >= 5)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val // 1 >= 5, f"Expected {x_val} // 1 >= 5"


def test_intexpr_rfloordiv_int():
    """Test int // IntExpr (reverse floor division)."""
    model = cp.Model()
    x = model.int_var(min=2, max=5, name="x")
    z = 20 // x
    model.constraint(z >= 4)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert 20 // x_val >= 4, f"Expected 20 // {x_val} >= 4"


def test_intexpr_rfloordiv_bool():
    """Test bool // IntExpr (reverse floor division)."""
    model = cp.Model()
    x = model.int_var(min=1, max=1, name="x")
    z = True // x  # True is treated as 1
    model.constraint(z == 1)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert 1 // x_val == 1, f"Expected 1 // {x_val} == 1"


def test_intexpr_neg():
    """Test -IntExpr (negation)."""
    model = cp.Model()
    x = model.int_var(min=-10, max=-5, name="x")
    z = -x
    model.constraint(z >= 5)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert -x_val >= 5, f"Expected -{x_val} >= 5"


def test_intexpr_lt_intexpr():
    """Test IntExpr < IntExpr."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    y = model.int_var(min=5, max=15, name="y")
    model.constraint(x < y)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    y_val = sol.get_value(y)
    assert y_val is not None
    assert x_val < y_val, f"Expected {x_val} < {y_val}"


def test_intexpr_lt_int():
    """Test IntExpr < int."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    model.constraint(x < 5)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val < 5, f"Expected {x_val} < 5"


def test_intexpr_le_intexpr():
    """Test IntExpr <= IntExpr."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    y = model.int_var(min=5, max=15, name="y")
    model.constraint(x <= y)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    y_val = sol.get_value(y)
    assert y_val is not None
    assert x_val <= y_val, f"Expected {x_val} <= {y_val}"


def test_intexpr_le_int():
    """Test IntExpr <= int."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    model.constraint(x <= 5)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val <= 5, f"Expected {x_val} <= 5"


def test_intexpr_gt_intexpr():
    """Test IntExpr > IntExpr."""
    model = cp.Model()
    x = model.int_var(min=5, max=15, name="x")
    y = model.int_var(min=0, max=10, name="y")
    model.constraint(x > y)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    y_val = sol.get_value(y)
    assert y_val is not None
    assert x_val > y_val, f"Expected {x_val} > {y_val}"


def test_intexpr_gt_int():
    """Test IntExpr > int."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    model.constraint(x > 5)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val > 5, f"Expected {x_val} > 5"


def test_intexpr_ge_intexpr():
    """Test IntExpr >= IntExpr."""
    model = cp.Model()
    x = model.int_var(min=5, max=15, name="x")
    y = model.int_var(min=0, max=10, name="y")
    model.constraint(x >= y)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    y_val = sol.get_value(y)
    assert y_val is not None
    assert x_val >= y_val, f"Expected {x_val} >= {y_val}"


def test_intexpr_ge_int():
    """Test IntExpr >= int."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    model.constraint(x >= 5)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val >= 5, f"Expected {x_val} >= 5"


def test_intexpr_eq_intexpr():
    """Test IntExpr == IntExpr."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    y = model.int_var(min=0, max=10, name="y")
    model.constraint(x == y)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    y_val = sol.get_value(y)
    assert y_val is not None
    assert x_val == y_val, f"Expected {x_val} == {y_val}"


def test_intexpr_eq_int():
    """Test IntExpr == int."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    model.constraint(x == 5)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val == 5, f"Expected {x_val} == 5"


def test_intexpr_ne_intexpr():
    """Test IntExpr != IntExpr."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    y = model.int_var(min=0, max=10, name="y")
    model.constraint(x != y)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    y_val = sol.get_value(y)
    assert y_val is not None
    assert x_val != y_val, f"Expected {x_val} != {y_val}"


def test_intexpr_ne_int():
    """Test IntExpr != int."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    model.constraint(x != 5)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val != 5, f"Expected {x_val} != 5"


def test_boolexpr_invert():
    """Test ~BoolExpr (invert/not)."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    b = x < 5
    model.constraint(~b)  # x >= 5

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val >= 5, f"Expected {x_val} >= 5"


def test_boolexpr_or_boolexpr():
    """Test BoolExpr | BoolExpr."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    y = model.int_var(min=0, max=10, name="y")
    b1 = x < 3
    b2 = y > 7
    model.constraint(b1 | b2)  # x < 3 OR y > 7

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val < 3, f"Expected {x_val} < 3"


def test_boolexpr_or_bool():
    """Test BoolExpr | bool."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    b = x < 3
    model.constraint(b | False)  # Equivalent to b

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val < 3, f"Expected {x_val} < 3"


def test_boolexpr_ror_bool():
    """Test bool | BoolExpr (reverse or)."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    b = x > 7
    model.constraint(False | b)  # Equivalent to b

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val > 7, f"Expected {x_val} > 7"


def test_boolexpr_and_boolexpr():
    """Test BoolExpr & BoolExpr."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    y = model.int_var(min=0, max=10, name="y")
    b1 = x >= 3
    b2 = y <= 7
    model.constraint(b1 & b2)  # x >= 3 AND y <= 7

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    y_val = sol.get_value(y)
    assert y_val is not None
    assert x_val >= 3 and y_val <= 7, f"Expected ({x_val} >= 3 AND {y_val} <= 7)"


def test_boolexpr_and_bool():
    """Test BoolExpr & bool."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    b = x >= 3
    model.constraint(b & True)  # Equivalent to b

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val >= 3, f"Expected {x_val} >= 3"


def test_boolexpr_rand_bool():
    """Test bool & BoolExpr (reverse and)."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    b = x <= 7
    model.constraint(True & b)  # Equivalent to b

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert x_val <= 7, f"Expected {x_val} <= 7"


def test_complex_expression():
    """Test complex combination of operators."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    y = model.int_var(min=0, max=10, name="y")
    z = model.int_var(min=0, max=20, name="z")

    # Complex: ((x + y) * 2 == z) AND (x < y) OR (z > 15)
    expr1 = (x + y) * 2 == z
    expr2 = x < y
    expr3 = z > 15
    model.constraint((expr1 & expr2) | expr3)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    y_val = sol.get_value(y)
    assert y_val is not None
    z_val = sol.get_value(z)
    assert z_val is not None
    # Check: ((x + y) * 2 == z) AND (x < y) OR (z > 15)
    expr1 = (x_val + y_val) * 2 == z_val
    expr2 = x_val < y_val
    expr3 = z_val > 15
    assert (expr1 and expr2) or expr3, f"Expected ((({x_val}+{y_val})*2=={z_val}) AND ({x_val}<{y_val})) OR ({z_val}>15)"


def test_intexpr_rlt_int():
    """Test int < IntExpr (reversed less-than)."""
    model = cp.Model()
    x = model.int_var(min=5, max=10, name="x")
    model.constraint(3 < x)  # x > 3

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert 3 < x_val, f"Expected 3 < {x_val}"


def test_intexpr_rle_int():
    """Test int <= IntExpr (reversed less-than-or-equal)."""
    model = cp.Model()
    x = model.int_var(min=5, max=10, name="x")
    model.constraint(5 <= x)  # x >= 5

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert 5 <= x_val, f"Expected 5 <= {x_val}"


def test_intexpr_rgt_int():
    """Test int > IntExpr (reversed greater-than)."""
    model = cp.Model()
    x = model.int_var(min=0, max=7, name="x")
    model.constraint(8 > x)  # x < 8

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert 8 > x_val, f"Expected 8 > {x_val}"


def test_intexpr_rge_int():
    """Test int >= IntExpr (reversed greater-than-or-equal)."""
    model = cp.Model()
    x = model.int_var(min=0, max=7, name="x")
    model.constraint(7 >= x)  # x <= 7

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert 7 >= x_val, f"Expected 7 >= {x_val}"


def test_intexpr_req_int():
    """Test int == IntExpr (reversed equality)."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    model.constraint(5 == x)  # x == 5

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert 5 == x_val, f"Expected 5 == {x_val}"


def test_intexpr_rne_int():
    """Test int != IntExpr (reversed not-equal)."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    model.constraint(5 != x)  # x != 5
    model.constraint(x >= 4)  # Constrain to narrow solution space
    model.constraint(x <= 6)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert 5 != x_val, f"Expected 5 != {x_val}"


def test_intexpr_reversed_combined():
    """Test combined reversed and normal comparisons."""
    model = cp.Model()
    x = model.int_var(min=0, max=10, name="x")
    # 3 < x < 7 using reversed and normal operators
    model.constraint(3 < x)
    model.constraint(x < 7)

    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"
    assert result.best_solution is not None
    sol = result.best_solution
    x_val = sol.get_value(x)
    assert x_val is not None
    assert 3 < x_val < 7, f"Expected 3 < {x_val} < 7"


def test_cumulexpr_le():
    """Test CumulExpr <= int - verify operator creates correct constraint."""
    model = cp.Model()
    x = model.interval_var(length=5, start=(0, 10), name="x")

    # Create a cumul expression and use <= operator
    cumul = model.pulse(x, 1)
    constraint = (cumul <= 1)

    # Verify constraint was created (it's a Constraint object)
    assert isinstance(constraint, cp.Constraint)
    # Verify it was added to the model
    assert constraint._get_props()['func'] == 'cumulLe'

    # Actually solve to verify it works
    model.minimize(model.start_of(x))
    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"


def test_cumulexpr_ge():
    """Test CumulExpr >= int - verify operator creates correct constraint."""
    model = cp.Model()
    x = model.interval_var(length=5, start=(0, 10), name="x")

    # Create a cumul expression and use >= operator
    cumul = model.step_at_start(x, 10)
    constraint = (cumul >= 0)

    # Verify constraint was created
    assert isinstance(constraint, cp.Constraint)
    # Verify it was added to the model
    assert constraint._get_props()['func'] == 'cumulGe'

    # Actually solve to verify it works
    model.minimize(model.start_of(x))
    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"


def test_cumulexpr_rle():
    """Test int <= CumulExpr (reversed less-than-or-equal) - verify operator creates correct constraint."""
    model = cp.Model()
    x = model.interval_var(length=5, start=(0, 10), name="x")

    # Create a cumul expression and use reversed <= operator
    cumul = model.step_at_start(x, 5)
    constraint = (0 <= cumul)  # Should translate to cumul >= 0

    # Verify constraint was created
    assert isinstance(constraint, cp.Constraint)
    # Verify it was added to the model as cumulGe
    assert constraint._get_props()['func'] == 'cumulGe'

    # Actually solve to verify it works
    model.minimize(model.start_of(x))
    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"


def test_cumulexpr_rge():
    """Test int >= CumulExpr (reversed greater-than-or-equal) - verify operator creates correct constraint."""
    model = cp.Model()
    x = model.interval_var(length=5, start=(0, 10), name="x")

    # Create a cumul expression and use reversed >= operator
    cumul = model.pulse(x, 1)
    constraint = (2 >= cumul)  # Should translate to cumul <= 2

    # Verify constraint was created
    assert isinstance(constraint, cp.Constraint)
    # Verify it was added to the model as cumulLe
    assert constraint._get_props()['func'] == 'cumulLe'

    # Actually solve to verify it works
    model.minimize(model.start_of(x))
    params = cp.Parameters()
    params.solutionLimit = 1
    result = cp.solve(model, params=params)

    assert result.nb_solutions == 1, "Should find a solution"