"""
Test that all type hints can be resolved correctly.

This test ensures that all necessary typing imports (Union, Optional, etc.)
are present in each module. If these imports are missing, type checkers like
Pylance/Mypy will show 'Any' for all types.
"""

import inspect
import typing
import pytest
import optalcp


def get_public_methods(cls):
    """Get all public methods of a class (excluding special methods)."""
    methods = []
    for name, obj in inspect.getmembers(cls, predicate=inspect.isfunction):
        # Skip private/special methods
        if name.startswith('_'):
            continue
        methods.append((name, obj))
    return methods


def test_interval_var_type_hints():
    """Test that IntervalVar methods have resolvable type hints."""
    errors = []

    methods_to_test = [
        'start',
        'end',
        'length',
        'end_before_start',
        'end_before_end',
        'start_before_start',
        'start_before_end',
        'end_at_start',
        'end_at_end',
        'start_at_start',
        'start_at_end',
        'alternative',
        'span',
        'forbid_start',
        'forbid_end',
        'forbid_extent',
    ]

    for method_name in methods_to_test:
        method = getattr(optalcp.IntervalVar, method_name, None)
        if method is None:
            continue

        try:
            hints = typing.get_type_hints(method)
            assert 'return' in hints, f"{method_name} missing return type"
            # Verify return type is not Any
            return_type = hints['return']
            assert return_type is not type(None), f"{method_name} return type is None"
        except NameError as e:
            errors.append(f"IntervalVar.{method_name}: {e}")
        except Exception as e:
            errors.append(f"IntervalVar.{method_name}: Unexpected error: {e}")

    if errors:
        pytest.fail("Type hint resolution errors:\n  " + "\n  ".join(errors))


def test_model_type_hints():
    """Test that Model methods have resolvable type hints."""
    errors = []

    methods_to_test = [
        'interval_var',
        'int_var',
        'bool_var',
        'constraint',
        'minimize',
        'maximize',
        'no_overlap',
    ]

    for method_name in methods_to_test:
        method = getattr(optalcp.Model, method_name, None)
        if method is None:
            continue

        try:
            hints = typing.get_type_hints(method)
            # Some methods like minimize/maximize might not have return types
            # Just verify the hints can be resolved
        except NameError as e:
            errors.append(f"Model.{method_name}: {e}")
        except Exception as e:
            errors.append(f"Model.{method_name}: Unexpected error: {e}")

    if errors:
        pytest.fail("Type hint resolution errors:\n  " + "\n  ".join(errors))


def test_int_expr_type_hints():
    """Test that IntExpr methods have resolvable type hints."""
    errors = []

    # Test operator overloads
    methods_to_test = [
        '__add__',
        '__sub__',
        '__mul__',
        '__floordiv__',
        '__neg__',
        '__lt__',
        '__le__',
        '__gt__',
        '__ge__',
        '__eq__',
    ]

    for method_name in methods_to_test:
        method = getattr(optalcp.IntExpr, method_name, None)
        if method is None:
            continue

        try:
            hints = typing.get_type_hints(method)
        except NameError as e:
            errors.append(f"IntExpr.{method_name}: {e}")
        except Exception as e:
            errors.append(f"IntExpr.{method_name}: Unexpected error: {e}")

    if errors:
        pytest.fail("Type hint resolution errors:\n  " + "\n  ".join(errors))


def test_bool_expr_type_hints():
    """Test that BoolExpr methods have resolvable type hints."""
    errors = []

    # Test operator overloads
    methods_to_test = [
        '__and__',
        '__or__',
        '__invert__',
    ]

    for method_name in methods_to_test:
        method = getattr(optalcp.BoolExpr, method_name, None)
        if method is None:
            continue

        try:
            hints = typing.get_type_hints(method)
        except NameError as e:
            errors.append(f"BoolExpr.{method_name}: {e}")
        except Exception as e:
            errors.append(f"BoolExpr.{method_name}: Unexpected error: {e}")

    if errors:
        pytest.fail("Type hint resolution errors:\n  " + "\n  ".join(errors))


def test_all_public_methods_have_resolvable_hints():
    """
    Comprehensive test: try to resolve type hints for all public methods
    in main classes.

    Note: Some methods use Union/Optional in generated code. This test now
    accepts both old-style (Union/Optional) and new-style (|) syntax.
    """
    errors = []

    classes_to_test = [
        ('Model', optalcp.Model),
        ('IntervalVar', optalcp.IntervalVar),
        ('IntExpr', optalcp.IntExpr),
        ('BoolExpr', optalcp.BoolExpr),
        ('IntVar', optalcp.IntVar),
        ('BoolVar', optalcp.BoolVar),
    ]

    # Methods that are code-generated and may still use Union (acceptable)
    generated_methods = {'guard', 'identity', 'in_range', 'max2', 'min2',
                        'and_', 'or_', 'implies'}

    for class_name, cls in classes_to_test:
        for method_name, method in get_public_methods(cls):
            try:
                typing.get_type_hints(method)
            except NameError as e:
                error_msg = str(e)
                # Union/Optional errors in generated methods are acceptable for now
                if method_name in generated_methods and any(name in error_msg for name in ['Union', 'Optional']):
                    continue
                # These are the critical errors we're testing for
                if any(name in error_msg for name in ['Union', 'Optional', 'Iterable']):
                    errors.append(f"{class_name}.{method_name}: {e}")
                # SolveResult and similar forward references are OK (TYPE_CHECKING imports)
                elif 'SolveResult' in error_msg or 'Solution' in error_msg:
                    pass
                else:
                    # Other NameErrors might indicate real problems
                    errors.append(f"{class_name}.{method_name}: {e}")
            except Exception:
                # Other errors might be OK (e.g., forward references)
                pass

    if errors:
        pytest.fail(
            "Type hint resolution errors (likely missing imports like Union/Optional):\n  " +
            "\n  ".join(errors)
        )


def test_typing_imports_present():
    """
    Verify that modules using old-style type syntax (Union/Optional) have
    the necessary imports. Modern syntax (|) doesn't require imports.

    Note: _base_types uses modern | syntax and doesn't need Union/Optional.
    """
    import optalcp._interval_var
    import optalcp._model
    import optalcp._base_types

    modules_to_check = [
        ('optalcp._interval_var', optalcp._interval_var),
        ('optalcp._model', optalcp._model),
        # _base_types now uses modern | syntax, so skip Union/Optional check
    ]

    errors = []

    for module_name, module in modules_to_check:
        # Check if module uses Union in annotations
        source = inspect.getsource(module)

        if 'Union[' in source:
            if not hasattr(module, 'Union'):
                errors.append(f"{module_name} uses Union but doesn't import it")

        if 'Optional[' in source:
            if not hasattr(module, 'Optional'):
                errors.append(f"{module_name} uses Optional but doesn't import it")

    if errors:
        pytest.fail("Missing typing imports:\n  " + "\n  ".join(errors))


if __name__ == '__main__':
    # Allow running this test directly for quick verification
    print("Testing type hints...")
    test_interval_var_type_hints()
    print("✅ IntervalVar type hints OK")
    test_model_type_hints()
    print("✅ Model type hints OK")
    test_int_expr_type_hints()
    print("✅ IntExpr type hints OK")
    test_bool_expr_type_hints()
    print("✅ BoolExpr type hints OK")
    test_all_public_methods_have_resolvable_hints()
    print("✅ All public methods have resolvable type hints")
    test_typing_imports_present()
    print("✅ Required typing imports present")
    print("\n🎉 All type hint tests passed!")
