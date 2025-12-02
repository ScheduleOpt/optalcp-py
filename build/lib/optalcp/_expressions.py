"""
Expression and element classes for OptalCP Python API.

This module contains ModelElement and expression classes (IntExpr, BoolExpr, CumulExpr).
Type definitions are in _types.py.
"""

from __future__ import annotations
from collections.abc import Iterable
from typing import TYPE_CHECKING
from ._constants import (
    IntVarMax,
    IntVarMin,
    IntervalMax,
    IntervalMin,
    LengthMax,
)
from ._types import (
    _ElementProps,
    _IndirectArgument,
    _ScalarArgument,
    _Argument,
    _wrap_int,
    _wrap_bool,
    _wrap_int_list,
    _wrap_int_matrix,
)

if TYPE_CHECKING:
    from ._model import Model
    from ._scheduling import IntStepFunction

# Re-export types and constants for backwards compatibility
__all__ = [
    # Constants (from _constants.py)
    'IntVarMax',
    'IntVarMin',
    'IntervalMax',
    'IntervalMin',
    'LengthMax',
    # Types (from _types.py)
    '_ElementProps',
    '_IndirectArgument',
    '_ScalarArgument',
    '_Argument',
    '_wrap_int',
    '_wrap_bool',
    '_wrap_int_list',
    '_wrap_int_matrix',
    # Expression classes
    'ModelElement',
    'Constraint',
    'IntExpr',
    'BoolExpr',
    'CumulExpr',
    'Directive',
    '_SearchDecision',
]


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

    def add(self) -> Constraint:
        """#doc[Constraint.add]"""
        self._model.add(self)
        return self


class IntExpr(ModelElement):
    r"""
    A class that represents an integer expression in the model.  The expression
    may depend on the value of a variable (or variables), so the value of the
    expression is not known until a solution is found.
    The value must be in the range :class:`IntVarMin` to :class:`IntVarMax`.

    The following code creates two interval variables `x` and `y`
    and an integer expression `maxEnd` that is equal to the maximum of the end
    times of `x` and `y` (see :meth:`IntExpr.max2`):

    ### Optional integer expressions

    Underlying variables of an integer expression may be optional, i.e., they may
    or may not be present in a solution (for example, an optional task
    can be omitted entirely from the solution). In this case, the value of the
    integer expression is *absent*. The value *absent* means that the variable
    has no meaning; it does not exist in the solution.

    Except :meth:`IntExpr.guard` expression, any value of an integer
    expression that depends on an absent variable is also *absent*.
    As we don't know the value of the expression before the solution is found,
    we call such expression *optional*.

    In the following model, there is an optional interval variable `x` and
    a non-optional interval variable `y`.  We add a constraint that the end of `x` plus
    10 must be less or equal to the start of `y`:

    In this model:

    * `endX` is an optional integer expression because it depends on
    an optional variable `x`.
    * The expression `afterX` is optional for the same reason.
    * The expression `startY` is not optional because it depends only on a
    non-optional variable `y`.
    * Boolean expression `isBefore` is also optional. Its value could be
    *true*, *false* or *absent*.

    The expression `isBefore` is turned into a constraint using
    :meth:`Model.constraint`. Therefore, it cannot be *false*
    in the solution. However, it can still be *absent*. Therefore the constraint
    `isBefore` can be satisfied in two ways:

    1. Both `x` and `y` are present, `x` is before `y`, and the delay between them
    is at least 10. In this case, `isBefore` is *true*.
    2. `x` is absent and `y` is present. In this case, `isBefore` is *absent*.
    """

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

    def _reusable_int_expr(self, ) -> IntExpr:
        out_params: list[_Argument] = [self._as_arg()]
        return IntExpr(self._model, "reusableIntExpr", out_params)

    def presence(self, ) -> BoolExpr:
        """#doc[IntExpr.presenceOf]"""
        out_params: list[_Argument] = [self._as_arg()]
        return BoolExpr(self._model, "intPresenceOf", out_params)

    def guard(self, absentValue: int | bool = 0) -> IntExpr:
        r"""
        Creates an expression that replaces value _absent_ by a constant.

        :param absentValue: The value to use when the expression is absent.
        :type absentValue: int

        :returns: The resulting integer expression
        :rtype: IntExpr

        The resulting expression is:

        * equal to the expression if the expression is *present*
        * and equal to `absentValue` otherwise (i.e. when the expression is *absent*).

        The default value of `absentValue` is 0.

        The resulting expression is never *absent*.

        Same as :meth:`Model.guard`.
        """
        out_params: list[_Argument] = [self._as_arg(), _wrap_int(absentValue)]
        return IntExpr(self._model, "intGuard", out_params)

    def identity(self, arg: IntExpr | int | bool) -> Constraint:
        r"""
        Identity is different than equality. presence status.

        :param arg2: The second integer expression.
        :type arg2: IntExpr

        :rtype: void

        Identity is different than equality. For example, if `x` is *absent*, then `x.eq(0)` is *absent*, but `x.identity(0)` is *false*.

        Same as :meth:`Model.identity`.
        """
        out_params: list[_Argument] = [self._as_arg(), IntExpr._wrap(arg)]
        return Constraint(self._model, "intIdentity", out_params)

    def in_range(self, lb: int | bool, ub: int | bool) -> BoolExpr:
        """#doc[IntExpr.inRange]"""
        out_params: list[_Argument] = [self._as_arg(), _wrap_int(lb), _wrap_int(ub)]
        return BoolExpr(self._model, "intInRange", out_params)

    def _not_in_range(self, lb: int | bool, ub: int | bool) -> BoolExpr:
        out_params: list[_Argument] = [self._as_arg(), _wrap_int(lb), _wrap_int(ub)]
        return BoolExpr(self._model, "intNotInRange", out_params)

    def abs(self, ) -> IntExpr:
        r"""
        Creates an integer expression which is absolute value of the expression.

        :returns: The resulting integer expression
        :rtype: IntExpr

        If the expression has value *absent*, the resulting expression also has value *absent*.

        Same as :meth:`Model.abs`.
        """
        out_params: list[_Argument] = [self._as_arg()]
        return IntExpr(self._model, "intAbs", out_params)

    def min2(self, arg: IntExpr | int | bool) -> IntExpr:
        r"""
        Creates an integer expression which is the minimum of the expression and `arg`.

        :param arg2: The second integer expression.
        :type arg2: IntExpr

        :returns: The resulting integer expression
        :rtype: IntExpr

        If the expression or `arg` has value *absent*, then the resulting expression has also value *absent*.

        Same as :meth:`Model.min2`. See :meth:`Model.min` for the n-ary minimum.
        """
        out_params: list[_Argument] = [self._as_arg(), IntExpr._wrap(arg)]
        return IntExpr(self._model, "intMin2", out_params)

    def max2(self, arg: IntExpr | int | bool) -> IntExpr:
        r"""
        Creates an integer expression which is the maximum of the expression and `arg`.

        :param arg2: The second integer expression.
        :type arg2: IntExpr

        :returns: The resulting integer expression
        :rtype: IntExpr

        If the expression or `arg` has value *absent*, then the resulting expression has also value *absent*.

        Same as :meth:`Model.max2`. See :meth:`Model.max` for n-ary maximum.
        """
        out_params: list[_Argument] = [self._as_arg(), IntExpr._wrap(arg)]
        return IntExpr(self._model, "intMax2", out_params)




class BoolExpr(IntExpr):
    r"""
    A class that represents a boolean expression in the model.
    The expression may depend on one or more variables; therefore, its value
    may be unknown until a solution is found.

    For example, the following code creates two interval variables, `x` and `y`
    and a boolean expression `isBefore` that is true if `x` ends before `y` starts,
    that is, if the end of `x` is less than or equal to
    the start of `y` (see :meth:`IntExpr.le`):

    Boolean expressions can be used to create constraints using function :meth:`Model.constraint`. In the example above, we may require that `isBefore` is
    true or *absent*:

    ### Optional boolean expressions

    *OptalCP* is using 3-value logic: a boolean expression can be *true*, *false*
    or *absent*. Typically, the expression is *absent* only if one or
    more underlying variables are *absent*.  The value *absent*
    means that the expression doesn't have a meaning because one or more
    underlying variables are absent (not part of the solution).

    ### Difference between constraints and boolean expressions

    Boolean expressions can take arbitrary value (*true*, *false*, or *absent*)
    and can be combined into composed expressions (e.g., using :meth:`BoolExpr.and_` or
    :meth:`BoolExpr.or_`).

    Constraints can only be *true* or *absent* (in a solution) and cannot
    be combined into composed expressions.

    Some functions create constraints directly, e.g. :meth:`Model.no_overlap`.
    Then, passing them to function :meth:`Model.constraint` is unnecessary.
    It is also not possible to combine constraints into composed expressions
    such as `or(noOverlap(..), noOverlap(..))`.

    Let's consider a similar example to the one above but with an optional interval
    variables `a` and `b`:

    The function :meth:`Model.constraint` requires that the
    constraint cannot be *false* in a solution. It could be *absent* though.
    Therefore, in our example, there are four kinds of solutions:

    1. Both `a` and `b` are present, and `a` ends before `b` starts.
    2. Only `a` is present, and `b` is absent.
    3. Only `b` is present, and `a` is absent.
    4. Both `a` and `b` are absent.

    In case 1, the expression `isBefore` is *true*. In all the other cases
    `isBefore` is *absent* as at least one of the variables `a` and `b` is
    absent, and then `isBefore` doesn't have a meaning.

    ### Boolean expressions as integer expressions

    Class `BoolExpr` derives from :class:`IntExpr`. Therefore, boolean expressions can be used
    as integer expressions. In this case, *true* is equal to *1*, *false* is
    equal to *0*, and *absent* remains *absent*.
    """

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

    def add(self) -> BoolExpr:
        """#doc[BoolExpr.add]"""
        self._model.add(self)
        return self

    def _reusable_bool_expr(self, ) -> BoolExpr:
        out_params: list[_Argument] = [self._as_arg()]
        return BoolExpr(self._model, "reusableBoolExpr", out_params)

    def not_(self, ) -> BoolExpr:
        r"""
        Returns negation of the expression.

        :returns: The resulting Boolean expression
        :rtype: BoolExpr

        If the expression has value *absent* then the resulting expression has also value *absent*.

        Same as :meth:`Model.not_`.
        """
        out_params: list[_Argument] = [self._as_arg()]
        return BoolExpr(self._model, "boolNot", out_params)

    def or_(self, arg: BoolExpr | bool) -> BoolExpr:
        r"""
        Returns logical _OR_ of the expression and `arg`.

        :param arg2: The second boolean expression.
        :type arg2: BoolExpr

        :returns: The resulting Boolean expression
        :rtype: BoolExpr

        If the expression or `arg` has value *absent* then the resulting expression has also value *absent*.

        Same as :meth:`Model.or_`.
        """
        out_params: list[_Argument] = [self._as_arg(), BoolExpr._wrap(arg)]
        return BoolExpr(self._model, "boolOr", out_params)

    def and_(self, arg: BoolExpr | bool) -> BoolExpr:
        r"""
        Returns logical _AND_ of the expression and `arg`.

        :param arg2: The second boolean expression.
        :type arg2: BoolExpr

        :returns: The resulting Boolean expression
        :rtype: BoolExpr

        If the expression or `arg` has value *absent*, then the resulting expression has also value *absent*.

        Same as :meth:`Model.and_`.
        """
        out_params: list[_Argument] = [self._as_arg(), BoolExpr._wrap(arg)]
        return BoolExpr(self._model, "boolAnd", out_params)

    def implies(self, arg: BoolExpr | bool) -> BoolExpr:
        r"""
        Returns implication between the expression and `arg`.

        :param arg2: The second boolean expression.
        :type arg2: BoolExpr

        :returns: The resulting Boolean expression
        :rtype: BoolExpr

        If the expression or `arg` has value *absent*, then the resulting expression has also value *absent*.

        Same as :meth:`Model.implies`.
        """
        out_params: list[_Argument] = [self._as_arg(), BoolExpr._wrap(arg)]
        return BoolExpr(self._model, "boolImplies", out_params)

    def _eq(self, arg: BoolExpr | bool) -> BoolExpr:
        out_params: list[_Argument] = [self._as_arg(), BoolExpr._wrap(arg)]
        return BoolExpr(self._model, "boolEq", out_params)

    def _ne(self, arg: BoolExpr | bool) -> BoolExpr:
        out_params: list[_Argument] = [self._as_arg(), BoolExpr._wrap(arg)]
        return BoolExpr(self._model, "boolNe", out_params)

    def _nand(self, arg: BoolExpr | bool) -> BoolExpr:
        out_params: list[_Argument] = [self._as_arg(), BoolExpr._wrap(arg)]
        return BoolExpr(self._model, "boolNand", out_params)




class CumulExpr(ModelElement):
    r"""
    Cumulative expression.

    Cumulative expression represents resource usage over time.  The resource
    could be a machine, a group of workers, a material, or anything of a limited
    capacity.  The resource usage is not known in advance as it depends on the
    variables of the problem.  Cumulative expressions allow us to model the resource
    usage and constrain it.

    Basic cumulative expressions are:

    * ***Pulse***: the resource is used over an interval of time.
    For example, a pulse can represent a task requiring a certain
    number of workers during its execution.  At the beginning of the interval,
    the resource usage increases by a given amount, and at the end of the
    interval, the resource usage decreases by the same amount.
    Pulse can be created by function :meth:`Model.pulse`
    or :meth:`IntervalVar.pulse`.
    * ***Step***: a given amount of resource is consumed or produced at a specified
    time (e.g., at the start of an interval variable).
    Steps may represent an inventory of a material that is
    consumed or produced by some tasks (a *reservoir*).
    Steps can be created by functions
    :meth:`Model.step_at_start`,
    :meth:`IntervalVar.step_at_start`,
    :meth:`Model.step_at_end`,
    :meth:`IntervalVar.step_at_end`. and
    :meth:`Model.step_at`.

    Cumulative expressions can be combined using
    :meth:`Model.cumul_plus`, :meth:`Model.cumul_minus`, :meth:`CumulExpr.cumul_neg` and
    :meth:`Model.cumul_sum`.  The resulting cumulative expression represents
    a sum of the resource usage of the combined expressions.

    Cumulative expressions can be constrained by :meth:`Model.cumul_ge` and
    :meth:`Model.cumul_le` constraints to specify the minimum and maximum
    allowed resource usage.

    See :meth:`Model.cumul_le` and :meth:`Model.cumul_ge` for examples.
    """

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

    def _cumul_max_profile(self, profile: IntStepFunction) -> Constraint:
        out_params: list[_Argument] = [self._as_arg(), IntStepFunction._wrap(profile)]
        return Constraint(self._model, "cumulMaxProfile", out_params)

    def _cumul_min_profile(self, profile: IntStepFunction) -> Constraint:
        out_params: list[_Argument] = [self._as_arg(), IntStepFunction._wrap(profile)]
        return Constraint(self._model, "cumulMinProfile", out_params)




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
