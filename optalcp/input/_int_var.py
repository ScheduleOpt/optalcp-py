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
    """#doc[IntVar]"""

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
