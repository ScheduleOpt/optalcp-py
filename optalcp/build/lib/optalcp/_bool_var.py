"""
Boolean variable classes for OptalCP Python API.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from ._base_types import BoolExpr, _ElementProps
from ._constants import _PresenceStatus

if TYPE_CHECKING:
    from ._model import Model


class BoolVar(BoolExpr):
    """

    """

    def __init__(self, model: Model, props: _ElementProps):
        self._model = model
        self._props = props
        self._arg = None
        self._force_ref()

    def is_optional(self) -> bool:
        """
        Returns True if the boolean variable was created as optional.
        Optional boolean variable can be absent in the solution, i.e., it can be omitted.

        Note: This function checks the presence status of the variable in the model
        (before the solve), not in the solution.

        See also: is_present(), is_absent()
        See also: make_optional(), make_present(), make_absent()
        """
        return self._props.get('status') == _PresenceStatus.Optional

    def is_present(self) -> bool:
        """
        Returns True if the boolean variable was created present (and
        therefore cannot be absent in the solution).

        Note: This function returns the presence status of the variable in the
        model (before the solve), not in the solution. In particular, for an
        optional boolean variable, this function returns False, even though there
        could be a solution in which the variable is present.

        See also: is_optional(), is_absent()
        See also: make_optional(), make_present(), make_absent()
        """
        status = self._props.get('status')
        return status is None or status == _PresenceStatus.Present

    def is_absent(self) -> bool:
        """
        Returns True if the boolean variable was created absent (and therefore
        cannot be present in the solution).

        Note: This function checks the presence status of the variable in the model
        (before the solve), not in the solution. In particular, for an optional
        boolean variable, this function returns False, even though there could be
        a solution in which the variable is absent.

        See also: is_optional(), is_present()
        See also: make_optional(), make_present(), make_absent()
        """
        return self._props.get('status') == _PresenceStatus.Absent

    def get_min(self) -> bool | None:
        """
        Returns the minimum value assigned to the boolean variable during its
        construction by Model.bool_var() or later by
        function set_min() or function set_range().

        If the variable is absent, the function returns None.
        For a free boolean variable (not constrained), returns False.
        If set_min(True) was called, the variable is fixed to True.

        Note: This function returns the minimum value of the variable in the
        model (before the solve), not in the solution.

        See also: get_max()
        See also: set_min(), set_max(), set_range()
        """
        if self.is_absent():
            return None
        return self._props.get('min', 0) > 0

    def get_max(self) -> bool | None:
        """
        Returns the maximum value assigned to the boolean variable during its
        construction by Model.bool_var() or later by
        function set_max() or function set_range().

        If the variable is absent, the function returns None.
        For a free boolean variable (not constrained), returns True.
        If set_max(False) was called, the variable is fixed to False.

        Note: This function returns the maximum value of the variable in the
        model (before the solve), not in the solution.

        See also: get_min()
        See also: set_min(), set_max(), set_range()
        """
        if self.is_absent():
            return None
        return self._props.get('max', 1) > 0

    def make_optional(self) -> None:
        """
        Makes the boolean variable optional. Optional boolean variable can be
        absent in the solution, i.e., can be omitted.

        See also: make_present(), make_absent()
        See also: is_optional(), is_present(), is_absent()
        """
        self._props['status'] = _PresenceStatus.Optional

    def make_absent(self) -> None:
        """
        Makes the boolean variable absent. Absent boolean variable cannot be
        present in the solution, i.e., it will be omitted in the solution (and
        everything that depends on it).

        See also: make_optional(), make_present()
        See also: is_optional(), is_present(), is_absent()
        """
        self._props['status'] = _PresenceStatus.Absent

    def make_present(self) -> None:
        """
        Makes the boolean variable present. The present boolean variable cannot be
        absent in the solution, i.e., cannot be omitted.

        See also: make_optional(), make_absent()
        See also: is_optional(), is_present(), is_absent()
        """
        self._props.pop('status', None)

    def set_min(self, min_val: bool) -> None:
        """
        Sets the minimum value of the boolean variable to the given value.

        It overwrites any previous minimum value limit given at variable creation by
        Model.bool_var() or later by set_min() or set_range().
        This function does not change the maximum value.

        Setting set_min(True) fixes the variable to True (since maximum is True by default).
        Setting set_min(False) has no effect on a free variable (since minimum is False by default).

        Args:
            min_val: Minimum value (True or False)

        See also: set_max(), set_range()
        See also: get_min(), get_max()
        """
        self._props['min'] = bool(min_val)

    def set_max(self, max_val: bool) -> None:
        """
        Sets the maximum value of the boolean variable to the given value.

        It overwrites any previous maximum value limit given at variable creation by
        Model.bool_var() or later by set_max() or set_range().
        This function does not change the minimum value.

        Setting set_max(False) fixes the variable to False (since minimum is False by default).
        Setting set_max(True) has no effect on a free variable (since maximum is True by default).

        Args:
            max_val: Maximum value (True or False)

        See also: set_min(), set_range()
        See also: get_min(), get_max()
        """
        self._props['max'] = bool(max_val)

    def set_range(self, min_val: bool, max_val: bool) -> None:
        """
        Sets the value of the boolean variable to the given range.

        It overwrites any previous value limits given at variable creation by
        Model.bool_var() or later by set_min(), set_max() or set_range().

        The call:
            bool_var.set_range(min_val, max_val)
        is equivalent to:
            bool_var.set_min(min_val)
            bool_var.set_max(max_val)

        Use set_range(True, True) to fix the variable to True.
        Use set_range(False, False) to fix the variable to False.
        Use set_range(False, True) to leave the variable free.

        Args:
            min_val: Minimum value (True or False)
            max_val: Maximum value (True or False)

        See also: set_min(), set_max()
        See also: get_min(), get_max()
        """
        self._props['min'] = bool(min_val)
        self._props['max'] = bool(max_val)
