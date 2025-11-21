"""
Core model classes for OptalCP Python API - Basic classes.
"""

from __future__ import annotations
from collections.abc import Iterable
from typing import Any, TypedDict, TYPE_CHECKING
from ._constants import _PresenceStatus, IntVarMin, IntVarMax, IntervalMin, IntervalMax, LengthMax # type: ignore[reportUnusedImport]

if TYPE_CHECKING:
    from ._model import Model
    from ._int_step_function import IntStepFunction

# Export public classes and constants for type checking
__all__ = [
    # Classes
    'ModelElement',
    'Constraint',
    'IntExpr',
    'BoolExpr',
    'CumulExpr',
    # Constants (re-exported from ._constants)
    'IntVarMin',
    'IntVarMax',
    'IntervalMin',
    'IntervalMax',
    'LengthMax',
]


# First define required fields
class _ElementPropsRequired(TypedDict):
    """Required properties that every model element must have."""
    func: str  # Function name (e.g., "intervalVar", "plus", "endOf")
    args: 'list[_Argument]'  # Forward reference to break circular dependency

# Then extend with optional fields
class _ElementProps(_ElementPropsRequired, total=False):
    """
    Properties of a model element for JSON serialization.
    Inherits required fields (func, args) and adds optional fields.
    """
    # Optional fields
    name: str
    status: int  # PresenceStatus
    # For IntVar and BoolVar:
    min: int | bool
    max: int | bool
    # For IntervalVar:
    startMin: int
    startMax: int
    endMin: int
    endMax: int
    lengthMin: int
    lengthMax: int
    # For IntStepFunction:
    values: list[list[int]]

class _IndirectArgument(TypedDict, total=False):
    """Represents an indirect argument with optional 'arg' (ElementProps) or 'ref' (reference ID)."""
    arg: _ElementProps  # Inlined expression
    ref: int  # Reference ID

_ScalarArgument = int | float | bool | _IndirectArgument
_Argument = _ScalarArgument | list[_ScalarArgument] | list[list[int]]

def _wrap_int(value: int | bool) -> _ScalarArgument:
    """Internal: Ensure the value is an integer."""
    if not isinstance(value, (int, bool)): # type: ignore[misc]
        raise TypeError(f"Expected int or bool. Got {type(value).__name__}")
    return value

def _wrap_bool(value: bool) -> _ScalarArgument:
    """Internal: Ensure the value is a boolean."""
    if not isinstance(value, bool): # type: ignore[misc]
        raise TypeError(f"Expected bool. Got {type(value).__name__}")
    return value

def _wrap_int_list(values: Iterable[int | bool]) -> list[_ScalarArgument]: # type: ignore[reportUnusedFunction]
    """
    Internal: Ensure the values are a list of integers.
    Copy the array so that if the user changes it in the future, we are not affected by the change.
    """
    # Validate all elements first
    for v in values:
        if not isinstance(v, (int, bool)): # type: ignore[misc]
            raise TypeError(f"Expected list of int or bool. Got {type(v).__name__}")
    # Then make a shallow copy
    return list(values)

def _wrap_int_matrix(values: Iterable[Iterable[int | bool]]) -> _Argument: # type: ignore[reportUnusedFunction]
    """
    Internal: Ensure the values are a matrix (list of lists) of integers.
    Copy the matrix so that if the user changes it in the future, we are not affected by the change.
    """
    # Validate all elements first
    for row in values:
        for v in row:
            if not isinstance(v, (int, bool)): # type: ignore[misc]
                raise TypeError(f"Expected list of list of int or bool. Got {type(v).__name__}")
    # Then make a deep copy using list comprehensions
    return [[int(v) for v in row] for row in values]


class ModelElement:
    """#doc[ModelElement]"""

    def __init__(self, model: Model, func: str, args: list[_Argument]):
        """
        Create a new model element.

        Args:
            model: The model this element belongs to
            func: Function name (e.g., "intervalVar", "plus", "endOf")
            args: Arguments to the function
        """
        self._model = model
        self._props: _ElementProps = {
            'func': func,
            'args': args
        }
        # How this node is referred when used in an expression
        # None: not used yet
        # {'arg': props}: used once (inlined)
        # {'ref': id}: used multiple times (referenced by ID)
        self._arg: _IndirectArgument | None = None

    @property
    def name(self) -> str | None:
        """
        Get or set the name assigned to the element.

        Returns:
            The name, or None if not named
        """
        return self._props.get('name')

    @name.setter
    def name(self, value: str) -> None:
        """
        Set the name of the element.

        Args:
            value: Name to assign
        """
        if not isinstance(value, str):
            raise TypeError(f"Element name must be str, got {type(value).__name__}")
        self._props['name'] = value

    def _get_props(self) -> _ElementProps:
        """Internal: Get the element properties for serialization."""
        return self._props

    def _as_arg(self) -> _IndirectArgument:
        """
        Internal: Get the argument representation for this element.

        First use: inline the element as {'arg': props}
        Second use: create a reference ID and return {'ref': id}
        """
        if self._arg is None:
            # First time this element is used in an expression
            self._arg = {'arg': self._props}
        elif 'ref' not in self._arg:
            # Second time the element is used - create a reference
            ref_id = self._model._get_new_ref_id(self._props)
            self._arg = {'ref': ref_id}
        return self._arg

    def _force_ref(self) -> None:
        """Internal: Force this element to have a reference ID (for variables)."""
        ref_id = self._model._get_new_ref_id(self._props)
        self._arg = {'ref': ref_id}

    def _get_id(self) -> int:
        """Internal: Get the reference ID of this element."""
        assert self._arg is not None and 'ref' in self._arg
        return self._arg['ref']


class Constraint(ModelElement):
    """
    Represents a constraint in the model.

    Constraints are automatically added to the model when created.
    """

    def __init__(self, model: Model, func: str, args: list[_Argument]):
        super().__init__(model, func, args)
        # Automatically add this constraint to the model
        model._add_constraint(self)


class IntExpr(ModelElement):
    """#doc[IntExpr]"""

    @staticmethod
    def _wrap(expr: int | bool | IntExpr) -> _ScalarArgument:
        """Internal: Convert an int or IntExpr to an argument."""
        if isinstance(expr, (int, bool)):
            return expr
        if isinstance(expr, IntExpr): # type: ignore[misc]
            return expr._as_arg()
        raise TypeError(f"Expected IntExpr, int, or bool. Got {type(expr).__name__}")

    @staticmethod
    def _wrap_list(exprs: Iterable[int | bool | IntExpr]) -> _Argument:
        """Internal: Convert a list of int/bool/IntExpr to a list of arguments (makes a copy)."""
        return [IntExpr._wrap(e) for e in exprs]

    def __add__(self, other: IntExpr | int | bool) -> IntExpr:
        """Add this expression to another expression or constant."""
        return IntExpr(self._model, 'intPlus', [self._as_arg(), IntExpr._wrap(other)])

    def __radd__(self, other: int | bool) -> IntExpr:
        """Add another constant to this expression."""
        return IntExpr(self._model, 'intPlus', [_wrap_int(other), self._as_arg()])

    def __sub__(self, other: IntExpr | int | bool) -> IntExpr:
        """Subtract another expression or constant from this expression."""
        return IntExpr(self._model, 'intMinus', [self._as_arg(), IntExpr._wrap(other)])

    def __rsub__(self, other: int | bool) -> IntExpr:
        """Subtract this expression from another constant."""
        return IntExpr(self._model, 'intMinus', [_wrap_int(other), self._as_arg()])

    def __mul__(self, other: IntExpr | int | bool) -> IntExpr:
        """Multiply this expression by another expression or constant."""
        return IntExpr(self._model, 'intTimes', [self._as_arg(), IntExpr._wrap(other)])

    def __rmul__(self, other: int | bool) -> IntExpr:
        """Multiply another constant by this expression."""
        return IntExpr(self._model, 'intTimes', [_wrap_int(other), self._as_arg()])

    def __floordiv__(self, other: IntExpr | int | bool) -> IntExpr:
        """Integer division of this expression by another expression or constant."""
        return IntExpr(self._model, 'intDiv', [self._as_arg(), IntExpr._wrap(other)])

    def __rfloordiv__(self, other: int | bool) -> IntExpr:
        """Integer division of a constant by this expression."""
        return IntExpr(self._model, 'intDiv', [_wrap_int(other), self._as_arg()])

    def __neg__(self) -> IntExpr:
        """Negate this expression."""
        return IntExpr(self._model, 'intNeg', [self._as_arg()])

    def __lt__(self, other: int | IntExpr) -> BoolExpr:
        """Create a less-than constraint."""
        if isinstance(other, int):
            return BoolExpr(self._model, 'intLt', [self._as_arg(), other])
        return BoolExpr(self._model, 'intLt', [self._as_arg(), other._as_arg()])

    def __le__(self, other: int | IntExpr) -> BoolExpr:
        """Create a less-than-or-equal constraint."""
        if isinstance(other, int):
            return BoolExpr(self._model, 'intLe', [self._as_arg(), other])
        return BoolExpr(self._model, 'intLe', [self._as_arg(), other._as_arg()])

    def __gt__(self, other: int | IntExpr) -> BoolExpr:
        """Create a greater-than boolean expression."""
        if isinstance(other, int):
            return BoolExpr(self._model, 'intGt', [self._as_arg(), other])
        return BoolExpr(self._model, 'intGt', [self._as_arg(), other._as_arg()])

    def __ge__(self, other: int | IntExpr) -> BoolExpr:
        """Create a greater-than-or-equal boolean expression."""
        if isinstance(other, int):
            return BoolExpr(self._model, 'intGe', [self._as_arg(), other])
        return BoolExpr(self._model, 'intGe', [self._as_arg(), other._as_arg()])

    def __eq__(self, other: int | IntExpr) -> BoolExpr:  # type: ignore
        """Create an equality boolean expression."""
        if isinstance(other, int):
            return BoolExpr(self._model, 'intEq', [self._as_arg(), other])
        return BoolExpr(self._model, 'intEq', [self._as_arg(), other._as_arg()])

    def __ne__(self, other: int | IntExpr) -> BoolExpr:  # type: ignore
        """Create a not-equal boolean expression."""
        if isinstance(other, int):
            return BoolExpr(self._model, 'intNe', [self._as_arg(), other])
        return BoolExpr(self._model, 'intNe', [self._as_arg(), other._as_arg()])

    def __rlt__(self, other: int | bool) -> BoolExpr:
        """Reversed less-than: for '5 < x', equivalent to 'x > 5'."""
        return BoolExpr(self._model, 'intGt', [self._as_arg(), _wrap_int(other)])

    def __rle__(self, other: int | bool) -> BoolExpr:
        """Reversed less-than-or-equal: for '5 <= x', equivalent to 'x >= 5'."""
        return BoolExpr(self._model, 'intGe', [self._as_arg(), _wrap_int(other)])

    def __rgt__(self, other: int | bool) -> BoolExpr:
        """Reversed greater-than: for '5 > x', equivalent to 'x < 5'."""
        return BoolExpr(self._model, 'intLt', [self._as_arg(), _wrap_int(other)])

    def __rge__(self, other: int | bool) -> BoolExpr:
        """Reversed greater-than-or-equal: for '5 >= x', equivalent to 'x <= 5'."""
        return BoolExpr(self._model, 'intLe', [self._as_arg(), _wrap_int(other)])

    def __req__(self, other: int | bool) -> BoolExpr:
        """Reversed equality: for '5 == x', equivalent to 'x == 5'."""
        return BoolExpr(self._model, 'intEq', [self._as_arg(), _wrap_int(other)])

    def __rne__(self, other: int | bool) -> BoolExpr:
        """Reversed not-equal: for '5 != x', equivalent to 'x != 5'."""
        return BoolExpr(self._model, 'intNe', [self._as_arg(), _wrap_int(other)])

    #include(intExpr)


class BoolExpr(IntExpr):
    """#doc[BoolExpr]"""

    @staticmethod
    def _wrap(expr: bool | BoolExpr) -> _ScalarArgument: # type: ignore[override]
        """Internal: Convert a bool or BoolExpr to an argument."""
        if isinstance(expr, bool):
            return expr
        if isinstance(expr, BoolExpr): # type: ignore[misc]
            return expr._as_arg()
        raise TypeError(f"Expected BoolExpr or bool. Got {type(expr).__name__}")

    @staticmethod
    def _wrap_list(exprs: Iterable[bool | BoolExpr]) -> _Argument: # type: ignore[override]
        """Internal: Convert a list of bool/BoolExpr to a list of arguments (makes a copy)."""
        return [BoolExpr._wrap(e) for e in exprs]

    def __invert__(self) -> BoolExpr:
        """Logical NOT operator (~). Returns negation of the expression."""
        return BoolExpr(self._model, 'boolNot', [self._as_arg()])

    def __or__(self, other: bool | BoolExpr) -> BoolExpr:
        """Logical OR operator (|)."""
        return BoolExpr(self._model, 'boolOr', [self._as_arg(), BoolExpr._wrap(other)])

    def __ror__(self, other: bool) -> BoolExpr:
        """Reverse logical OR operator."""
        return BoolExpr(self._model, 'boolOr', [_wrap_bool(other), self._as_arg()])

    def __and__(self, other: bool | BoolExpr) -> BoolExpr:
        """Logical AND operator (&)."""
        return BoolExpr(self._model, 'boolAnd', [self._as_arg(), BoolExpr._wrap(other)])

    def __rand__(self, other: bool) -> BoolExpr:
        """Reverse logical AND operator."""
        return BoolExpr(self._model, 'boolAnd', [_wrap_bool(other), self._as_arg()])

    #include(boolExpr)


class CumulExpr(ModelElement):
    """#doc[CumulExpr]"""

    @staticmethod
    def _wrap(expr: CumulExpr) -> _ScalarArgument:
        """Internal: Convert a CumulExpr to an argument."""
        if isinstance(expr, CumulExpr): # type: ignore[misc]
            return expr._as_arg()
        raise TypeError(f"Expected CumulExpr. Got {type(expr).__name__}")

    @staticmethod
    def _wrap_list(exprs: Iterable[CumulExpr]) -> _Argument:
        """Internal: Convert a list of CumulExpr to a list of arguments (makes a copy)."""
        return [CumulExpr._wrap(e) for e in exprs]

    def __add__(self, other: CumulExpr) -> CumulExpr:
        """Add two cumulative expressions."""
        return CumulExpr(self._model, 'cumulPlus', [self._as_arg(), CumulExpr._wrap(other)])

    def __sub__(self, other: CumulExpr) -> CumulExpr:
        """Subtract cumulative expression from another."""
        return CumulExpr(self._model, 'cumulMinus', [self._as_arg(), CumulExpr._wrap(other)])

    def __neg__(self) -> CumulExpr:
        """Negate cumulative expression."""
        return CumulExpr(self._model, 'cumulNeg', [self._as_arg()])

    def __le__(self, other: int | bool) -> Constraint:
        """Less-than-or-equal constraint: cumul <= capacity."""
        return Constraint(self._model, 'cumulLe', [self._as_arg(), _wrap_int(other)])

    def __ge__(self, other: int | bool) -> Constraint:
        """Greater-than-or-equal constraint: cumul >= capacity."""
        return Constraint(self._model, 'cumulGe', [self._as_arg(), _wrap_int(other)])

    def __rle__(self, other: int | bool) -> Constraint:
        """Reversed less-than-or-equal: for 'capacity <= cumul', equivalent to 'cumul >= capacity'."""
        return Constraint(self._model, 'cumulGe', [self._as_arg(), _wrap_int(other)])

    def __rge__(self, other: int | bool) -> Constraint:
        """Reversed greater-than-or-equal: for 'capacity >= cumul', equivalent to 'cumul <= capacity'."""
        return Constraint(self._model, 'cumulLe', [self._as_arg(), _wrap_int(other)])

    #include(cumulExpr)


class _SearchDecision(ModelElement): # type: ignore[reportUnusedClass]
    @staticmethod
    def _wrap(expr: _SearchDecision) -> _ScalarArgument:
        if isinstance(expr, _SearchDecision): # type: ignore[misc]
            return expr._as_arg()
        raise TypeError(f"Expected _SearchDecision. Got {type(expr).__name__}")
    @staticmethod
    def _wrap_list(exprs: Iterable[_SearchDecision]) -> _Argument:
        return [_SearchDecision._wrap(e) for e in exprs]


class Directive(ModelElement): # type: ignore[reportUnusedClass]
    def __init__(self, model: Model, func: str, args: list[_Argument]):
        super().__init__(model, func, args)
        # Automatically add this directive to the model
        model._add_directive(self)
