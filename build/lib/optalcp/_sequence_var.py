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
    """
    Models a sequence (order) of interval variables.

    Sequence variable is used with :meth:`Model.no_overlap` constraint
    to ensure that some interval variables do not overlap.
    Such no-overlapping set of interval variables will form a sequence in the solution.
    The sequence variable captures this order of interval variables
    and allows additional constraints on the order to be stated.

    .. seealso::

        - :meth:`Model.position.`.
    """

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
        """
        Constrain the interval variables forming the sequence to not overlap.

        :param transitions: 2D square array of minimum transition distances between the intervals. The first index is the type (index) of the first interval in the sequence, the second index is the type (index) of the second interval in the sequence
        :type transitions: number[][]

        :returns: The no-overlap constraint.
        :rtype: Constraint

        The `noOverlap` constraint makes sure that the intervals in the sequence
        do not overlap.  That is, for every pair of interval variables `x` and `y`
        at least one of the following conditions must hold (in a solution):

        1. Interval variable `x` is *absent*. This means that the interval is not
        present in the solution (not performed), so it cannot overlap
        with any other interval. Only optional interval variables can be *absent*.
        2. Interval variable `y` is *absent*.
        3. `x` ends before `y` starts, i.e. `x.end()` is less or equal to `y.start()`.
        4. `y` ends before `x` starts, i.e. `y.end()` is less or equal to `x.start()`.

        In addition, if the `transitions` parameter is specified, then the cases 3 and 4
        are further constrained by the minimum transition distance between the
        intervals:

        3. `x.end() + transitions[x.type][y.type]` is less or equal to `y.start()`.
        4. `y.end() + transitions[y.type][x.type]` is less or equal to `x.start()`.

        where `x.type` and `y.type` are the types of the interval variables `x` and `y`
        as given in :meth:`Model.sequence_var`. If types were not specified,
        then they are equal to the indices of the interval variables in the array
        passed to :meth:`Model.sequence_var`. Transition times
        cannot be negative.

        Note that transition times are enforced between every pair of interval variables,
        not only between direct neighbors.

        The size of the 2D array `transitions` must be equal to the number of types
        of the interval variables.

        This constraint is the same as
        :meth:`Model.no_overlap`.
        Constraint
        :meth:`Model.no_overlap`
        is also the same but specifies the intervals directly instead of using
        a sequence variable.

        A worker must perform a set of tasks. Each task is characterized by:

        * `length` of the task (how long it takes to perform it),
        * `location` of the task (where it must be performed),
        * a time window `startMin` to `endMax` when the task must be performed.

        There are three locations, `0`, `1`, and `2`. The minimum travel times between
        the locations are given by a transition matrix `transitions`. Transition times
        are not symmetric. For example, it takes 10 minutes to travel from location `0`
        to location `1` but 15 minutes to travel back from location `1` to location `0`.

        We will model this problem using `noOverlap` constraint with transition times.
        """
        if transitions is None:
            return Constraint(self._model, 'noOverlap', [self._as_arg()])
        else:
            return Constraint(self._model, 'noOverlap', [self._as_arg(), _wrap_int_matrix(transitions)])

    def _same_sequence(self, sequence2: SequenceVar) -> Constraint:
        out_params: list[_Argument] = [self._as_arg(), SequenceVar._wrap(sequence2)]
        return Constraint(self._model, "sameSequence", out_params)


