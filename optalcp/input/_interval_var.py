"""
Interval variable classes for OptalCP Python API.
"""

from __future__ import annotations
from collections.abc import Iterable
from typing import TYPE_CHECKING
from ._base_types import ModelElement, IntExpr, BoolExpr, CumulExpr, Constraint, _ScalarArgument, _ElementProps, _wrap_int, _wrap_int_list, _wrap_int_matrix
from ._constants import _PresenceStatus, IntervalMin, IntervalMax, LengthMax
from ._int_step_function import IntStepFunction
from ._sequence_var import SequenceVar

if TYPE_CHECKING:
    from ._model import Model
    from ._base_types import _Argument, Directive

class IntervalVar(ModelElement):
    """#doc[IntervalVar]"""

    def __init__(self, model: Model, props: _ElementProps):
        self._model = model
        self._props = props
        self._arg = None
        self._force_ref()

    @staticmethod
    def _wrap(expr: IntervalVar) -> _ScalarArgument:
        """Internal: Convert a CumulExpr to an argument."""
        if isinstance(expr, IntervalVar): # type: ignore[misc]
            return expr._as_arg()
        raise TypeError(f"Expected IntervalVar. Got {type(expr).__name__}")

    @staticmethod
    def _wrap_list(exprs: Iterable[IntervalVar]) -> list[_ScalarArgument]:
        return [IntervalVar._wrap(e) for e in exprs]

    #include(intervalVar)

    # Presence status queries
    def is_optional(self) -> bool:
        """#doc[IntervalVar.isOptional]"""
        return self._props.get('status') == _PresenceStatus.Optional

    def is_present(self) -> bool:
        """#doc[IntervalVar.isPresent]"""
        status = self._props.get('status')
        return status is None or status == _PresenceStatus.Present

    def is_absent(self) -> bool:
        """#doc[IntervalVar.isAbsent]"""
        return self._props.get('status') == _PresenceStatus.Absent

    # Getters for domain bounds
    def get_start_min(self) -> int | None:
        """#doc[IntervalVar.getStartMin]"""
        if self.is_absent():
            return None
        return self._props.get('startMin', IntervalMin)

    def get_start_max(self) -> int | None:
        """#doc[IntervalVar.getStartMax]"""
        if self.is_absent():
            return None
        return self._props.get('startMax', IntervalMax)

    def get_end_min(self) -> int | None:
        """#doc[IntervalVar.getEndMin]"""
        if self.is_absent():
            return None
        return self._props.get('endMin', IntervalMin)

    def get_end_max(self) -> int | None:
        """#doc[IntervalVar.getEndMax]"""
        if self.is_absent():
            return None
        return self._props.get('endMax', IntervalMax)

    def get_length_min(self) -> int | None:
        """#doc[IntervalVar.getLengthMin]"""
        if self.is_absent():
            return None
        return self._props.get('lengthMin', 0)

    def get_length_max(self) -> int | None:
        """#doc[IntervalVar.getLengthMax]"""
        if self.is_absent():
            return None
        return self._props.get('lengthMax', LengthMax)

    # Modifiers
    def make_optional(self) -> None:
        """#doc[IntervalVar.makeOptional]"""
        self._props['status'] = _PresenceStatus.Optional

    def make_present(self) -> None:
        """#doc[IntervalVar.makePresent]"""
        self._props.pop('status', None)

    def make_absent(self) -> None:
        """#doc[IntervalVar.makeAbsent]"""
        self._props['status'] = _PresenceStatus.Absent

    # Start setters
    def set_start(self, s_min: int, s_max: int | None = None) -> None:
        """#doc[IntervalVar.setStart]"""
        self._props['startMin'] = int(s_min)
        if s_max is None:
            self._props['startMax'] = int(s_min)
        else:
            self._props['startMax'] = int(s_max)

    def set_start_min(self, s_min: int) -> None:
        """#doc[IntervalVar.setStartMin]"""
        self._props['startMin'] = int(s_min)

    def set_start_max(self, s_max: int) -> None:
        """#doc[IntervalVar.setStartMax]"""
        self._props['startMax'] = int(s_max)

    # End setters
    def set_end(self, e_min: int, e_max: int | None = None) -> None:
        """#doc[IntervalVar.setEnd]"""
        self._props['endMin'] = int(e_min)
        if e_max is None:
            self._props['endMax'] = int(e_min)
        else:
            self._props['endMax'] = int(e_max)

    def set_end_min(self, e_min: int) -> None:
        """#doc[IntervalVar.setEndMin]"""
        self._props['endMin'] = int(e_min)

    def set_end_max(self, e_max: int) -> None:
        """#doc[IntervalVar.setEndMax]"""
        self._props['endMax'] = int(e_max)

    # Length setters
    def set_length(self, l_min: int, l_max: int | None = None) -> None:
        """#doc[IntervalVar.setLength]"""
        self._props['lengthMin'] = int(l_min)
        if l_max is None:
            self._props['lengthMax'] = int(l_min)
        else:
            self._props['lengthMax'] = int(l_max)

    def set_length_min(self, l_min: int) -> None:
        """#doc[IntervalVar.setLengthMin]"""
        self._props['lengthMin'] = int(l_min)

    def set_length_max(self, l_max: int) -> None:
        """#doc[IntervalVar.setLengthMax]"""
        self._props['lengthMax'] = int(l_max)
