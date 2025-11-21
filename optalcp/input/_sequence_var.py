"""
Sequence variable class for OptalCP Python API.
"""

from __future__ import annotations
from collections.abc import Iterable
from typing import TYPE_CHECKING
from ._base_types import ModelElement, Constraint, _Argument, _ScalarArgument, _wrap_int_matrix

if TYPE_CHECKING:
    from ._model import Model

class SequenceVar(ModelElement):
    """#doc[SequenceVar]"""

    def __init__(self, model: 'Model', func: str, args: list[_Argument]):
        super().__init__(model, func, args)
        self._force_ref()

    def _make_auxiliary(self) -> None:
        """Internal: Mark this sequence as auxiliary."""
        self._props['func'] = '_sequenceVar'

    @staticmethod
    def _wrap(expr: SequenceVar) -> _ScalarArgument:
        """Internal: Convert a SequenceVar to an argument."""
        if isinstance(expr, SequenceVar): # type: ignore[misc]
            return expr._as_arg()
        raise TypeError(f"Expected SequenceVar. Got {type(expr).__name__}")
    @staticmethod
    def _wrap_list(exprs: Iterable[SequenceVar]) -> _Argument:
        return [SequenceVar._wrap(e) for e in exprs]

    def no_overlap(self, transitions: Iterable[Iterable[int]] | None = None) -> Constraint:
        """#doc[SequenceVar.noOverlap]"""
        if transitions is None:
            return Constraint(self._model, 'noOverlap', [self._as_arg()])
        else:
            return Constraint(self._model, 'noOverlap', [self._as_arg(), _wrap_int_matrix(transitions)])

    #include(sequenceVar)
