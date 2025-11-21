"""
Integer variable classes for OptalCP Python API.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from ._base_types import IntExpr, _ElementProps
from ._constants import _PresenceStatus, IntVarMin, IntVarMax

if TYPE_CHECKING:
    from ._model import Model

class IntVar(IntExpr):
    """
    Integer variable represents an unknown (integer) value that solver has to find.

    The value of the integer variable can be constrained using mathematical expressions, such as :meth:`Model.plus`, :meth:`Model.times`, :meth:`Model.le`, :meth:`Model.sum`.

    OptalCP solver focuses on scheduling problems and concentrates on :class:`IntervalVar` variables.
    Therefore, interval variables should be the primary choice for modeling in OptalCP.
    However, integer variables can be used for other purposes, such as counting or indexing.
    In particular, integer variables can be helpful for cumulative expressions with variable heights; see :meth:`Model.pulse`, :meth:`Model.step_at_start`, :meth:`Model.step_at_end`, and :meth:`Model.step_at`.

    The integer variable can be optional.
    In this case, the solver can make the variable absent, which is usually interpreted as the fact that the solver does not use the variable at all.
    Functions :meth:`Model.presence_of` and :meth:`IntExpr.presence` can constrain the presence of the variable.

    Integer variables can be created using the function :meth:`Model.int_var`.

    In the following example we create three integer variables `x`, `y` and `z`.
    Variables `x` and `y` are present, but variable `z` is optional.
    Each variable has a different range of possible values.
    """

    def __init__(self, model: Model, props: _ElementProps):
        # Don't call super().__init__ - we're creating from props directly
        self._model = model
        self._props = props
        self._arg = None
        # Variables always get a reference ID
        self._force_ref()

    def is_optional(self) -> bool:
        """
        Returns True if the integer variable was created as optional.
        Optional integer variable can be absent in the solution, i.e., it can be omitted.

        Note: This function checks the presence status of the variable in the model
        (before the solve), not in the solution.

        See also: is_present(), is_absent()
        See also: make_optional(), make_present(), make_absent()
        """
        return self._props.get('status') == _PresenceStatus.Optional

    def is_present(self) -> bool:
        """
        Returns True if the integer variable was created present (and
        therefore cannot be absent in the solution).

        Note: This function returns the presence status of the variable in the
        model (before the solve), not in the solution. In particular, for an
        optional integer variable, this function returns False, even though there
        could be a solution in which the variable is present.

        See also: is_optional(), is_absent()
        See also: make_optional(), make_present(), make_absent()
        """
        status = self._props.get('status')
        return status is None or status == _PresenceStatus.Present

    def is_absent(self) -> bool:
        """
        Returns True if the integer variable was created absent (and therefore
        cannot be present in the solution).

        Note: This function checks the presence status of the variable in the model
        (before the solve), not in the solution. In particular, for an optional
        integer variable, this function returns False, even though there could be
        a solution in which the variable is absent.

        See also: is_optional(), is_present()
        See also: make_optional(), make_present(), make_absent()
        """
        return self._props.get('status') == _PresenceStatus.Absent

    def get_min(self) -> int | None:
        """
        Returns the minimum value assigned to the integer variable during its
        construction by Model.int_var() or later by
        function set_min() or function set_range().

        If the variable is absent, the function returns None.

        Note: This function returns the minimum value of the variable in the
        model (before the solve), not in the solution.

        See also: get_max()
        See also: set_min(), set_max(), set_range()
        """
        if self.is_absent():
            return None
        return self._props.get('min', IntVarMin)

    def get_max(self) -> int | None:
        """
        Returns the maximum value assigned to the integer variable during its
        construction by Model.int_var() or later by
        function set_max() or function set_range().

        If the variable is absent, the function returns None.

        Note: This function returns the maximum value of the variable in the
        model (before the solve), not in the solution.

        See also: get_min()
        See also: set_min(), set_max(), set_range()
        """
        if self.is_absent():
            return None
        return self._props.get('max', IntVarMax)

    def make_optional(self) -> None:
        """
        Makes the integer variable optional. Optional integer variable can be
        absent in the solution, i.e., can be omitted.

        See also: make_present(), make_absent()
        See also: is_optional(), is_present(), is_absent()
        """
        self._props['status'] = _PresenceStatus.Optional

    def make_absent(self) -> None:
        """
        Makes the integer variable absent. Absent integer variable cannot be
        present in the solution, i.e., it will be omitted in the solution (and
        everything that depends on it).

        See also: make_optional(), make_present()
        See also: is_optional(), is_present(), is_absent()
        """
        self._props['status'] = _PresenceStatus.Absent

    def make_present(self) -> None:
        """
        Makes the integer variable present. The present integer variable cannot be
        absent in the solution, i.e., cannot be omitted.

        See also: make_optional(), make_absent()
        See also: is_optional(), is_present(), is_absent()
        """
        self._props.pop('status', None)

    def set_min(self, min_val: int) -> None:
        """
        Sets the minimum value of the integer variable to the given value.

        It overwrites any previous minimum value limit given at variable creation by
        Model.int_var() or later by set_min() or set_range().
        This function does not change the maximum value.

        Note that the value of the integer variable must be in the range IntVarMin to IntVarMax.

        Args:
            min_val: Minimum value

        See also: set_max(), set_range()
        See also: get_min(), get_max()
        """
        self._props['min'] = int(min_val)

    def set_max(self, max_val: int) -> None:
        """
        Sets the maximum value of the integer variable to the given value.

        It overwrites any previous maximum value limit given at variable creation by
        Model.int_var() or later by set_max() or set_range().
        This function does not change the minimum value.

        Note that the value of the integer variable must be in the range IntVarMin to IntVarMax.

        Args:
            max_val: Maximum value

        See also: set_min(), set_range()
        See also: get_min(), get_max()
        """
        self._props['max'] = int(max_val)

    def set_range(self, min_val: int, max_val: int) -> None:
        """
        Sets the value of the integer variable to the given range.

        It overwrites any previous value limits given at variable creation by
        Model.int_var() or later by set_min(), set_max() or set_range().

        The call:
            int_var.set_range(min_val, max_val)
        is equivalent to:
            int_var.set_min(min_val)
            int_var.set_max(max_val)

        Note that the value of the integer variable must be in the range IntVarMin to IntVarMax.

        Args:
            min_val: Minimum value
            max_val: Maximum value

        See also: set_min(), set_max()
        See also: get_min(), get_max()
        """
        self._props['min'] = int(min_val)
        self._props['max'] = int(max_val)
