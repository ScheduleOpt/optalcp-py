"""
Scheduling-related variable classes for OptalCP Python API.

This module contains:
- IntStepFunction: Step functions for scheduling
- SequenceVar: Sequence variables for ordering tasks
- IntervalVar: Interval variables for representing tasks
"""

from __future__ import annotations
from collections.abc import Iterable
from typing import TYPE_CHECKING
from ._expressions import (
    ModelElement,
    IntExpr,
    BoolExpr,
    CumulExpr,
    Constraint,
    _ScalarArgument,
    _ElementProps,
    _Argument,
    _wrap_int,
    _wrap_int_list,
    _wrap_int_matrix,
)
from ._constants import _PresenceStatus, IntervalMin, IntervalMax, LengthMax

if TYPE_CHECKING:
    from ._model import Model
    from ._expressions import Directive


# =============================================================================
# IntStepFunction
# =============================================================================

class IntStepFunction(ModelElement):
    r"""
    Integer step function.

    Integer step function is a piecewise constant function defined on integer
    values in range :class:`IntVarMin` to :class:`IntVarMax`. The function can be
    created by :meth:`Model.step_function`.

    Step functions can be used in the following ways:

    * Function :meth:`Model.step_function_eval` evaluates the function at the given point (given as :class:`IntExpr`).
    * Function :meth:`Model.step_function_sum` computes a sum (integral) of the function over an :class:`IntervalVar`.
    * Constraints :meth:`Model.forbid_start` and :meth:`Model.forbid_end` forbid the start/end of an :class:`IntervalVar` to be in a zero-value interval of the function.
    * Constraint :meth:`Model.forbid_extent` forbids the extent of an :class:`IntervalVar` to be in a zero-value interval of the function.
    """

    def __init__(self, model: Model, values: Iterable[tuple[int, int]]):
        """
        Create a new integer step function.

        Args:
            model: The model this function belongs to
            values: Iterable of (value, next_point) pairs. Each pair defines that the function
                   has the given value until next_point is reached. Both value and next_point
                   must be integers.

        Raises:
            TypeError: If any item is not a pair of integers
            ValueError: If any item does not have exactly 2 elements
        """
        super().__init__(model, "intStepFunction", [])

        # Validate and copy the array so the user cannot change it later
        validated_values: list[list[int]] = []
        for i, item in enumerate(values):
            # Check if item is a sequence with exactly 2 elements
            if not hasattr(item, '__len__'):
                raise ValueError(f"Step function item at index {i} must be a sequence of 2 integers (value, next_point), got non-sequence: {repr(item)}")
            if len(item) != 2:
                raise ValueError(f"Step function item at index {i} must have exactly 2 elements (value, next_point), got {len(item)}: {repr(item)}")

            # Extract the two values
            val, next_point = item

            # Validate both are integers
            if not isinstance(val, int): # type: ignore[misc]
                raise TypeError(f"Step function value at index {i} must be an integer, got {type(val).__name__}")
            if not isinstance(next_point, int): # type: ignore[misc]
                raise TypeError(f"Step function next_point at index {i} must be an integer, got {type(next_point).__name__}")

            # Store as a list [value, next_point] to match the JSON format
            validated_values.append([val, next_point])

        self._props['values'] = validated_values

    @staticmethod
    def _wrap(expr: IntStepFunction) -> _ScalarArgument:
        """Internal: Convert a IntStepFunction to an argument."""
        if isinstance(expr, IntStepFunction): # type: ignore[misc]
            return expr._as_arg()
        raise TypeError(f"Expected IntStepFunction. Got {type(expr).__name__}")

    def step_function_sum(self, interval: IntervalVar) -> IntExpr:
        """#doc[IntStepFunction.stepFunctionSum]"""
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap(interval)]
        return IntExpr(self._model, "intStepFunctionSum", out_params)

    def _step_function_sum_in_range(self, interval: IntervalVar, lb: int | bool, ub: int | bool) -> Constraint:
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap(interval), _wrap_int(lb), _wrap_int(ub)]
        return Constraint(self._model, "intStepFunctionSumInRange", out_params)

    def step_function_eval(self, arg: IntExpr | int | bool) -> IntExpr:
        """#doc[IntStepFunction.stepFunctionEval]"""
        out_params: list[_Argument] = [self._as_arg(), IntExpr._wrap(arg)]
        return IntExpr(self._model, "intStepFunctionEval", out_params)

    def _step_function_eval_in_range(self, arg: IntExpr | int | bool, lb: int | bool, ub: int | bool) -> Constraint:
        out_params: list[_Argument] = [self._as_arg(), IntExpr._wrap(arg), _wrap_int(lb), _wrap_int(ub)]
        return Constraint(self._model, "intStepFunctionEvalInRange", out_params)

    def _step_function_eval_not_in_range(self, arg: IntExpr | int | bool, lb: int | bool, ub: int | bool) -> Constraint:
        out_params: list[_Argument] = [self._as_arg(), IntExpr._wrap(arg), _wrap_int(lb), _wrap_int(ub)]
        return Constraint(self._model, "intStepFunctionEvalNotInRange", out_params)




# =============================================================================
# SequenceVar
# =============================================================================

class SequenceVar(ModelElement):
    r"""
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
        r"""
        Constrain the interval variables forming the sequence to not overlap.

        :param transitions: 2D square array of minimum transition distances between the intervals. The first index is the type (index) of the first interval in the sequence, the second index is the type (index) of the second interval in the sequence
        :type transitions: number[][]

        :returns: The no-overlap constraint.
        :rtype: Constraint

        The `no_overlap` constraint makes sure that the intervals in the sequence
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

        We will model this problem using `no_overlap` constraint with transition times.
        """
        if transitions is None:
            return Constraint(self._model, 'noOverlap', [self._as_arg()])
        else:
            return Constraint(self._model, 'noOverlap', [self._as_arg(), _wrap_int_matrix(transitions)])

    def _same_sequence(self, sequence2: SequenceVar) -> Constraint:
        out_params: list[_Argument] = [self._as_arg(), SequenceVar._wrap(sequence2)]
        return Constraint(self._model, "sameSequence", out_params)




# =============================================================================
# IntervalVar
# =============================================================================

class IntervalVar(ModelElement):
    r"""
    Interval variable is a task, action, operation, or any other interval with a start
    and an end. The start and the end of the interval are unknowns that the solver
    has to find. They could be accessed as integer expressions using
    :meth:`IntervalVar.start` and :meth:`IntervalVar.end`.
    or using :meth:`Model.start` and :meth:`Model.end`.
    In addition to the start and the end of the interval, the interval variable
    has a length (equal to *end - start*) that can be accessed using
    :meth:`IntervalVar.length` or :meth:`Model.length`.

    The interval variable can be optional. In this case, the solver can decide
    to make the interval absent, which is usually interpreted as the fact that
    the interval doesn't exist, the task/action was not executed, or the operation
    was not performed.  When the interval variable is absent, its start, end,
    and length are also absent.  A boolean expression that represents the presence
    of the interval variable can be accessed using
    :meth:`IntervalVar.presence` and :meth:`Model.presence_of`.

    Interval variables can be created using the function
    :meth:`Model.interval_var`.
    By default, interval variables are *present* (not optional).
    To create an optional interval, specify `optional: true` in the
    arguments of the function.

    @example: present interval variables

    In the following example we create three present interval variables `x`, `y` and `z`
    and we make sure that they don't overlap.  Then, we minimize the maximum of
    the end times of the three intervals (the makespan):

    @example: optional interval variables

    In the following example, there is a task *X* that could be performed by two
    different workers *A* and *B*.  The interval variable `X` represents the task.
    It is not optional because the task `X` is mandatory. Interval variable
    `XA` represents the task `X` when performed by worker *A* and
    similarly `XB` represents the task `X` when performed by worker *B*.
    Both `XA` and `XB` are optional because it is not known beforehand which
    worker will perform the task.  The constraint :meth:`IntervalVar.alternative` links
    `X`, `XA` and `XB` together and ensures that only one of `XA` and `XB` is present and that
    `X` and the present interval are equal.

    Variables `XA` and `XB` can be used elsewhere in the model, e.g. to make sure
    that each worker is assigned to at most one task at a time:
    """

    def __init__(self, model: Model, props: _ElementProps, ref_id: int | None = None):
        self._model = model
        self._props = props
        self._arg = None
        if ref_id is not None:
            # Loading from JSON - use existing ref_id
            self._arg = {'ref': ref_id}
        else:
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

    def presence(self, ) -> BoolExpr:
        """#doc[IntervalVar.presenceOf]"""
        out_params: list[_Argument] = [self._as_arg()]
        return BoolExpr(self._model, "intervalPresenceOf", out_params)

    def start(self, ) -> IntExpr:
        r"""
        Creates an integer expression for the start time of the interval variable.

        :param interval: The interval variable.
        :type interval: IntervalVar

        :returns: The resulting integer expression
        :rtype: IntExpr

        If the interval variable is absent, then the resulting expression is also absent.

        In the following example, we constraint interval variable `y` to start after the end of `y` with a delay of at least 10. In addition, we constrain the length of `x` to be less or equal to the length of `y`.

        When `x` or `y` is *absent* then value of both constraints above is *absent* and therefore they are satisfied.

        .. seealso::

            - :meth:`Model.start` is equivalent function on :class:`Model`.
            - Function :meth:`IntervalVar.start_or_else` is a similar function that replaces value _absent_ by a constant.
        """
        out_params: list[_Argument] = [self._as_arg()]
        return IntExpr(self._model, "startOf", out_params)

    def end(self, ) -> IntExpr:
        r"""
        Creates an integer expression for the end time of the interval variable.

        :param interval: The interval variable.
        :type interval: IntervalVar

        :returns: The resulting integer expression
        :rtype: IntExpr

        If the interval variable is absent, then the resulting expression is also absent.

        In the following example, we constraint interval variable `y` to start after the end of `y` with a delay of at least 10. In addition, we constrain the length of `x` to be less or equal to the length of `y`.

        When `x` or `y` is *absent* then value of both constraints above is *absent* and therefore they are satisfied.

        .. seealso::

            - :meth:`Model.end` is equivalent function on :class:`Model`.
            - Function :meth:`IntervalVar.end_or_else` is a similar function that replaces value _absent_ by a constant.
        """
        out_params: list[_Argument] = [self._as_arg()]
        return IntExpr(self._model, "endOf", out_params)

    def length(self, ) -> IntExpr:
        r"""
        Creates an integer expression for the duration (end - start) of the interval variable.

        :param interval: The interval variable.
        :type interval: IntervalVar

        :returns: The resulting integer expression
        :rtype: IntExpr

        If the interval variable is absent, then the resulting expression is also absent.

        In the following example, we constraint interval variable `y` to start after the end of `y` with a delay of at least 10. In addition, we constrain the length of `x` to be less or equal to the length of `y`.

        When `x` or `y` is *absent* then value of both constraints above is *absent* and therefore they are satisfied.

        .. seealso::

            - :meth:`Model.length` is equivalent function on :class:`Model`.
            - Function :meth:`IntervalVar.length_or_else` is a similar function that replaces value _absent_ by a constant.
        """
        out_params: list[_Argument] = [self._as_arg()]
        return IntExpr(self._model, "lengthOf", out_params)

    def start_or_else(self, absentValue: int | bool) -> IntExpr:
        r"""
        Creates an integer expression for the start time of the interval variable. If the interval is absent, then its value is `absentValue`.

        :param absentValue: The value to use when the interval is absent.
        :type absentValue: int

        :returns: The resulting integer expression
        :rtype: IntExpr

        This function is equivalent to `interval.start().guard(absentValue)`.

        .. seealso::

            - :meth:`IntervalVar.start`
            - :meth:`IntervalVar.guard`
        """
        out_params: list[_Argument] = [self._as_arg(), _wrap_int(absentValue)]
        return IntExpr(self._model, "startOr", out_params)

    def end_or_else(self, absentValue: int | bool) -> IntExpr:
        r"""
        Creates an integer expression for the end time of the interval variable. If the interval is absent, then its value is `absentValue`.

        :param absentValue: The value to use when the interval is absent.
        :type absentValue: int

        :returns: The resulting integer expression
        :rtype: IntExpr

        This function is equivalent to `interval.end().guard(absentValue)`.

        .. seealso::

            - :meth:`IntervalVar.end`
            - :meth:`IntervalVar.guard`
        """
        out_params: list[_Argument] = [self._as_arg(), _wrap_int(absentValue)]
        return IntExpr(self._model, "endOr", out_params)

    def length_or_else(self, absentValue: int | bool) -> IntExpr:
        r"""
        Creates an integer expression for the duration (end - start) of the interval variable. If the interval is absent, then its value is `absentValue`.

        :param absentValue: The value to use when the interval is absent.
        :type absentValue: int

        :returns: The resulting integer expression
        :rtype: IntExpr

        This function is equivalent to `interval.length().guard(absentValue)`.

        .. seealso::

            - :meth:`IntervalVar.length`
            - :meth:`IntervalVar.guard`
        """
        out_params: list[_Argument] = [self._as_arg(), _wrap_int(absentValue)]
        return IntExpr(self._model, "lengthOr", out_params)

    def _alternative_cost(self, options: Iterable[IntervalVar], weights: Iterable[int | bool]) -> IntExpr:
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap_list(options), _wrap_int_list(weights)]
        return IntExpr(self._model, "intAlternativeCost", out_params)

    def end_before_end(self, successor: IntervalVar, delay: IntExpr | int | bool = 0) -> Constraint:
        r"""
        Creates a precedence constraint between two interval variables.

        :param successor: The successor interval variable.
        :type successor: IntervalVar
        :param delay: The minimum delay between intervals.
        :type delay: IntExpr

        :returns: The precedence constraint.
        :rtype: Constraint

        Assuming that the current interval is `predecessor`, the constraint is the same as:

        In other words, end of `predecessor` plus `delay` must be less than or equal to end of `successor`.

        When one of the two interval variables is absent, then the constraint is satisfied.

        .. seealso::

            - :meth:`Model.end_before_end` is equivalent function on :class:`Model`.
            - :meth:`Model.constraint`
            - :meth:`IntervalVar.start`, :meth:`IntervalVar.end`
            - :meth:`IntExpr.le`
        """
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap(successor), IntExpr._wrap(delay)]
        return Constraint(self._model, "endBeforeEnd", out_params)

    def end_before_start(self, successor: IntervalVar, delay: IntExpr | int | bool = 0) -> Constraint:
        r"""
        Creates a precedence constraint between two interval variables.

        :param successor: The successor interval variable.
        :type successor: IntervalVar
        :param delay: The minimum delay between intervals.
        :type delay: IntExpr

        :returns: The precedence constraint.
        :rtype: Constraint

        Assuming that the current interval is `predecessor`, the constraint is the same as:

        In other words, end of `predecessor` plus `delay` must be less than or equal to start of `successor`.

        When one of the two interval variables is absent, then the constraint is satisfied.

        .. seealso::

            - :meth:`Model.end_before_start` is equivalent function on :class:`Model`.
            - :meth:`Model.constraint`
            - :meth:`IntervalVar.start`, :meth:`IntervalVar.end`
            - :meth:`IntExpr.le`
        """
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap(successor), IntExpr._wrap(delay)]
        return Constraint(self._model, "endBeforeStart", out_params)

    def start_before_end(self, successor: IntervalVar, delay: IntExpr | int | bool = 0) -> Constraint:
        r"""
        Creates a precedence constraint between two interval variables.

        :param successor: The successor interval variable.
        :type successor: IntervalVar
        :param delay: The minimum delay between intervals.
        :type delay: IntExpr

        :returns: The precedence constraint.
        :rtype: Constraint

        Assuming that the current interval is `predecessor`, the constraint is the same as:

        In other words, start of `predecessor` plus `delay` must be less than or equal to end of `successor`.

        When one of the two interval variables is absent, then the constraint is satisfied.

        .. seealso::

            - :meth:`Model.start_before_end` is equivalent function on :class:`Model`.
            - :meth:`Model.constraint`
            - :meth:`IntervalVar.start`, :meth:`IntervalVar.end`
            - :meth:`IntExpr.le`
        """
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap(successor), IntExpr._wrap(delay)]
        return Constraint(self._model, "startBeforeEnd", out_params)

    def start_before_start(self, successor: IntervalVar, delay: IntExpr | int | bool = 0) -> Constraint:
        r"""
        Creates a precedence constraint between two interval variables.

        :param successor: The successor interval variable.
        :type successor: IntervalVar
        :param delay: The minimum delay between intervals.
        :type delay: IntExpr

        :returns: The precedence constraint.
        :rtype: Constraint

        Assuming that the current interval is `predecessor`, the constraint is the same as:

        In other words, start of `predecessor` plus `delay` must be less than or equal to start of `successor`.

        When one of the two interval variables is absent, then the constraint is satisfied.

        .. seealso::

            - :meth:`Model.start_before_start` is equivalent function on :class:`Model`.
            - :meth:`Model.constraint`
            - :meth:`IntervalVar.start`, :meth:`IntervalVar.end`
            - :meth:`IntExpr.le`
        """
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap(successor), IntExpr._wrap(delay)]
        return Constraint(self._model, "startBeforeStart", out_params)

    def end_at_end(self, successor: IntervalVar, delay: IntExpr | int | bool = 0) -> Constraint:
        r"""
        Creates a precedence constraint between two interval variables.

        :param successor: The successor interval variable.
        :type successor: IntervalVar
        :param delay: The minimum delay between intervals.
        :type delay: IntExpr

        :returns: The precedence constraint.
        :rtype: Constraint

        Assuming that the current interval is `predecessor`, the constraint is the same as:

        In other words, end of `predecessor` plus `delay` must be equal to end of `successor`.

        When one of the two interval variables is absent, then the constraint is satisfied.

        .. seealso::

            - :meth:`Model.end_at_end` is equivalent function on :class:`Model`.
            - :meth:`Model.constraint`
            - :meth:`IntervalVar.start`, :meth:`IntervalVar.end`
            - :meth:`IntExpr.eq`
        """
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap(successor), IntExpr._wrap(delay)]
        return Constraint(self._model, "endAtEnd", out_params)

    def end_at_start(self, successor: IntervalVar, delay: IntExpr | int | bool = 0) -> Constraint:
        r"""
        Creates a precedence constraint between two interval variables.

        :param successor: The successor interval variable.
        :type successor: IntervalVar
        :param delay: The minimum delay between intervals.
        :type delay: IntExpr

        :returns: The precedence constraint.
        :rtype: Constraint

        Assuming that the current interval is `predecessor`, the constraint is the same as:

        In other words, end of `predecessor` plus `delay` must be equal to start of `successor`.

        When one of the two interval variables is absent, then the constraint is satisfied.

        .. seealso::

            - :meth:`Model.end_at_start` is equivalent function on :class:`Model`.
            - :meth:`Model.constraint`
            - :meth:`IntervalVar.start`, :meth:`IntervalVar.end`
            - :meth:`IntExpr.eq`
        """
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap(successor), IntExpr._wrap(delay)]
        return Constraint(self._model, "endAtStart", out_params)

    def start_at_end(self, successor: IntervalVar, delay: IntExpr | int | bool = 0) -> Constraint:
        r"""
        Creates a precedence constraint between two interval variables.

        :param successor: The successor interval variable.
        :type successor: IntervalVar
        :param delay: The minimum delay between intervals.
        :type delay: IntExpr

        :returns: The precedence constraint.
        :rtype: Constraint

        Assuming that the current interval is `predecessor`, the constraint is the same as:

        In other words, start of `predecessor` plus `delay` must be equal to end of `successor`.

        When one of the two interval variables is absent, then the constraint is satisfied.

        .. seealso::

            - :meth:`Model.start_at_end` is equivalent function on :class:`Model`.
            - :meth:`Model.constraint`
            - :meth:`IntervalVar.start`, :meth:`IntervalVar.end`
            - :meth:`IntExpr.eq`
        """
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap(successor), IntExpr._wrap(delay)]
        return Constraint(self._model, "startAtEnd", out_params)

    def start_at_start(self, successor: IntervalVar, delay: IntExpr | int | bool = 0) -> Constraint:
        r"""
        Creates a precedence constraint between two interval variables.

        :param successor: The successor interval variable.
        :type successor: IntervalVar
        :param delay: The minimum delay between intervals.
        :type delay: IntExpr

        :returns: The precedence constraint.
        :rtype: Constraint

        Assuming that the current interval is `predecessor`, the constraint is the same as:

        In other words, start of `predecessor` plus `delay` must be equal to start of `successor`.

        When one of the two interval variables is absent, then the constraint is satisfied.

        .. seealso::

            - :meth:`Model.start_at_start` is equivalent function on :class:`Model`.
            - :meth:`Model.constraint`
            - :meth:`IntervalVar.start`, :meth:`IntervalVar.end`
            - :meth:`IntExpr.eq`
        """
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap(successor), IntExpr._wrap(delay)]
        return Constraint(self._model, "startAtStart", out_params)

    def alternative(self, options: Iterable[IntervalVar]) -> Constraint:
        r"""
        Creates alternative constraints for the interval variable and provided `options`.

        :param options: The interval variables to choose from.
        :type options: IntervalVar[]

        :returns: The alternative constraint.
        :rtype: Constraint

        This constraint is the same as :meth:`Model.alternative`.
        """
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap_list(options)]
        return Constraint(self._model, "alternative", out_params)

    def span(self, covered: Iterable[IntervalVar]) -> Constraint:
        r"""
        Constraints the interval variable to span (cover) a set of other interval variables.

        :param covered: The set of interval variables to cover.
        :type covered: IntervalVar[]

        :returns: The span constraint.
        :rtype: Constraint

        This constraint is the same as :meth:`Model.span`.
        """
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap_list(covered)]
        return Constraint(self._model, "span", out_params)

    def position(self, sequence: SequenceVar) -> IntExpr:
        r"""
        Creates an expression equal to the position of the interval on the sequence.

        :param sequence: The sequence variable.
        :type sequence: SequenceVar

        :returns: The resulting integer expression
        :rtype: IntExpr

        This function is the same as :meth:`Model.position`.
        """
        out_params: list[_Argument] = [self._as_arg(), SequenceVar._wrap(sequence)]
        return IntExpr(self._model, "position", out_params)

    def pulse(self, height: IntExpr | int | bool) -> CumulExpr:
        r"""
        Creates cumulative function (expression) pulse for the interval variable and specified height.

        :param height: The height value.
        :type height: IntExpr

        :returns: The resulting cumulative expression
        :rtype: CumulExpr

        Creates cumulative function (expression) *pulse* for the interval variable and specified height.

        This function is the same as :meth:`Model.pulse`.

        .. rubric:: Example

        .. code-block:: python

            task = model.interval_var(name="task", length=10)
            pulse = task.pulse(5)

        .. seealso::

            - :meth:`Model.pulse` for detailed documentation and examples.
        """
        out_params: list[_Argument] = [self._as_arg(), IntExpr._wrap(height)]
        return CumulExpr(self._model, "pulse", out_params)

    def step_at_start(self, height: IntExpr | int | bool) -> CumulExpr:
        r"""
        Creates cumulative function (expression) that changes value at start of the interval variable by the given height.

        :param height: The height value.
        :type height: IntExpr

        :returns: The resulting cumulative expression
        :rtype: CumulExpr

        Creates cumulative function (expression) that changes value at start of the interval variable by the given height.

        This function is the same as :meth:`Model.step_at_start`.

        .. rubric:: Example

        .. code-block:: python

            task = model.interval_var(name="task", length=10)
            step = task.step_at_start(5)

        .. seealso::

            - :meth:`Model.step_at_start` for detailed documentation.
            - :meth:`IntervalVar.step_at_end` for the opposite function.
        """
        out_params: list[_Argument] = [self._as_arg(), IntExpr._wrap(height)]
        return CumulExpr(self._model, "stepAtStart", out_params)

    def step_at_end(self, height: IntExpr | int | bool) -> CumulExpr:
        r"""
        Creates cumulative function (expression) that changes value at end of the interval variable by the given height.

        :param height: The height value.
        :type height: IntExpr

        :returns: The resulting cumulative expression
        :rtype: CumulExpr

        Creates cumulative function (expression) that changes value at end of the interval variable by the given height.

        This function is the same as :meth:`Model.step_at_end`.

        .. rubric:: Example

        .. code-block:: python

            task = model.interval_var(name="task", length=10)
            step = task.step_at_end(5)

        .. seealso::

            - :meth:`Model.step_at_end` for detailed documentation.
            - :meth:`IntervalVar.step_at_start` for the opposite function.
        """
        out_params: list[_Argument] = [self._as_arg(), IntExpr._wrap(height)]
        return CumulExpr(self._model, "stepAtEnd", out_params)

    def _precedence_energy_before(self, others: Iterable[IntervalVar], heights: Iterable[int | bool], capacity: int | bool) -> Constraint:
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap_list(others), _wrap_int_list(heights), _wrap_int(capacity)]
        return Constraint(self._model, "precedenceEnergyBefore", out_params)

    def _precedence_energy_after(self, others: Iterable[IntervalVar], heights: Iterable[int | bool], capacity: int | bool) -> Constraint:
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap_list(others), _wrap_int_list(heights), _wrap_int(capacity)]
        return Constraint(self._model, "precedenceEnergyAfter", out_params)

    def forbid_extent(self, func: IntStepFunction) -> Constraint:
        r"""
        This function prevents the specified interval variable from overlapping with segments of the step function where the value is zero. the value is zero.

        :param func: The step function.
        :type func: IntStepFunction

        :returns: The constraint forbidding the extent (entire interval).
        :rtype: Constraint

        This function prevents the specified interval variable from overlapping with segments of the step function where the value is zero. I.e., if :math:`[s, e)` is a segment of the step function where the value is zero, then the interval variable either ends before :math:`s` (:math:`\mathtt{interval.end()} \le s`) or starts after :math:`e` (:math:`e \le \mathtt{interval.start()}`).

        .. seealso::

            - :meth:`Model.forbid_extent` for the equivalent function on :class:`Model`.
            - :meth:`Model.forbid_start`, :meth:`Model.forbid_end` for similar functions that constrain the start/end of an interval variable.
            - :meth:`Model.step_function_eval` for evaluation of a step function.
        """
        out_params: list[_Argument] = [self._as_arg(), IntStepFunction._wrap(func)]
        return Constraint(self._model, "forbidExtent", out_params)

    def forbid_start(self, func: IntStepFunction) -> Constraint:
        r"""
        Constrains the start of an interval variable to not coincide with zero segments of a step function.

        :param func: 
        :type func: IntStepFunction

        :returns: The constraint forbidding the start point.
        :rtype: Constraint

        This function is equivalent to:

        I.e., the function value at the start of the interval variable cannot be zero.

        .. seealso::

            - :meth:`Model.forbid_start` for the equivalent function on :class:`Model`.
            - :meth:`Model.forbid_end` for similar function that constrains end an interval variable.
            - :meth:`Model.step_function_eval` for evaluation of a step function.
        """
        out_params: list[_Argument] = [self._as_arg(), IntStepFunction._wrap(func)]
        return Constraint(self._model, "forbidStart", out_params)

    def forbid_end(self, func: IntStepFunction) -> Constraint:
        r"""
        Constrains the end of an interval variable to not coincide with zero segments of a step function.

        :param func: 
        :type func: IntStepFunction

        :returns: The constraint forbidding the end point.
        :rtype: Constraint

        This function is equivalent to:

        I.e., the function value at the end of the interval variable cannot be zero.

        .. seealso::

            - :meth:`Model.forbid_end` for the equivalent function on :class:`Model`.
            - :meth:`Model.forbid_start` for similar function that constrains start an interval variable.
            - :meth:`Model.step_function_eval` for evaluation of a step function.
        """
        out_params: list[_Argument] = [self._as_arg(), IntStepFunction._wrap(func)]
        return Constraint(self._model, "forbidEnd", out_params)

    def _disjunctive_is_before(self, y: IntervalVar) -> BoolExpr:
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap(y)]
        return BoolExpr(self._model, "disjunctiveIsBefore", out_params)

    def _related(self, y: IntervalVar) -> Directive:
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap(y)]
        return Directive(self._model, "related", out_params)



    # Presence status queries
    def is_optional(self) -> bool:
        r"""
        Returns _true_ if the interval variable was created as _optional_.

        :returns: True if the interval is optional
        :rtype: boolean

        Returns *true* if the interval variable was created as *optional*.
        Optional interval variable can be *absent* in the solution, i.e., it can be omitted.

        **Note:** This function checks the presence status of the variable in the model
        (before the solve), not in the solution.

        .. seealso::

            - :meth:`IntervalVar.is_present`, :meth:`IntervalVar.is_absent`.
            - :meth:`IntervalVar.make_optional`, :meth:`IntervalVar.make_present`, :meth:`IntervalVar.make_absent`.
        """
        return self._props.get('status') == _PresenceStatus.Optional

    def is_present(self) -> bool:
        r"""
        Returns _true_ if the interval variable was created _present_ (and therefore cannot be _absent_ in the solution).

        :returns: True if the interval is present
        :rtype: boolean

        Returns *true* if the interval variable was created *present* (and
        therefore cannot be *absent* in the solution).

        **Note:** This function returns the presence status of the interval in the
        model (before the solve), not in the solution.  In particular, for an
        optional interval variable, this function returns *false*, even though there
        could be a solution in which the interval is *present*.

        .. seealso::

            - :meth:`IntervalVar.is_optional`, :meth:`IntervalVar.is_absent`.
            - :meth:`IntervalVar.make_optional`, :meth:`IntervalVar.make_present`, :meth:`IntervalVar.make_absent`.
        """
        status = self._props.get('status')
        return status is None or status == _PresenceStatus.Present

    def is_absent(self) -> bool:
        r"""
        Returns _true_ if the interval variable was created _absent_ (and therefore cannot be _present_ in the solution).

        :returns: True if the interval is absent
        :rtype: boolean

        Returns *true* if the interval variable was created *absent* (and therefore
        cannot be *present* in the solution).

        **Note:** This function checks the presence status of the interval in the model
        (before the solve), not in the solution.  In particular, for an optional
        interval variable, this function returns *false*, even though there could be
        a solution in which the interval is *absent*.

        .. seealso::

            - :meth:`IntervalVar.is_optional`, :meth:`IntervalVar.is_present`.
            - :meth:`IntervalVar.make_optional`, :meth:`IntervalVar.make_present`, :meth:`IntervalVar.make_absent`.
        """
        return self._props.get('status') == _PresenceStatus.Absent

    # Getters for domain bounds
    def get_start_min(self) -> int | None:
        r"""
        Returns minimum start value assigned to the interval variable during its construction by {@meth Model.intervalVar} or later by function {@meth IntervalVar.setStart} or function {@meth IntervalVar.setStartMin}.

        :returns: The start min value
        :rtype: number | null

        Returns minimum start value assigned to the interval variable during its
        construction by :meth:`Model.interval_var` or later by
        function :meth:`IntervalVar.set_start` or function :meth:`IntervalVar.set_start_min`.

        If the interval is absent, the function returns `null`.

        **Note:** This function returns the minimum start of the interval in the
        model (before the solve), not in the solution.
        """
        if self.is_absent():
            return None
        return self._props.get('startMin', IntervalMin)

    def get_start_max(self) -> int | None:
        r"""
        Returns maximum start value assigned to the interval variable during its construction by {@meth Model.intervalVar} or later by function {@meth IntervalVar.setStart} or function {@meth IntervalVar.setStartMax}.

        :returns: The start max value
        :rtype: number | null

        Returns maximum start value assigned to the interval variable during its
        construction by :meth:`Model.interval_var` or later by
        function :meth:`IntervalVar.set_start` or function :meth:`IntervalVar.set_start_max`.

        If the interval is absent, the function returns `null`.

        **Note:** This function returns the maximum start of the interval in the
        model (before the solve), not in the solution.
        """
        if self.is_absent():
            return None
        return self._props.get('startMax', IntervalMax)

    def get_end_min(self) -> int | None:
        r"""
        Returns minimum end assigned to the interval variable during its construction by {@meth Model.intervalVar} or later by function {@meth IntervalVar.setEnd} or function {@meth IntervalVar.setEndMin}.

        :returns: The end min value
        :rtype: number | null

        Returns minimum end assigned to the interval variable during its
        construction by :meth:`Model.interval_var` or later by
        function :meth:`IntervalVar.set_end` or function :meth:`IntervalVar.set_end_min`.

        If the interval is absent, the function returns `null`.

        **Note:** This function returns the minimum end of the interval in the
        model (before the solve), not in the solution.
        """
        if self.is_absent():
            return None
        return self._props.get('endMin', IntervalMin)

    def get_end_max(self) -> int | None:
        r"""
        Returns maximum end assigned to the interval variable during its construction by {@meth Model.intervalVar} or later by function {@meth IntervalVar.setEnd} or function {@meth IntervalVar.setEndMax}.

        :returns: The end max value
        :rtype: number | null

        Returns maximum end assigned to the interval variable during its
        construction by :meth:`Model.interval_var` or later by
        function :meth:`IntervalVar.set_end` or function :meth:`IntervalVar.set_end_max`.

        If the interval is absent, the function returns `null`.

        **Note:** This function returns the maximum end of the interval in the
        model (before the solve), not in the solution.
        """
        if self.is_absent():
            return None
        return self._props.get('endMax', IntervalMax)

    def get_length_min(self) -> int | None:
        r"""
        Returns minimum length assigned to the interval variable during its construction by {@meth Model.intervalVar} or later by function {@meth IntervalVar.setLength} or function {@meth IntervalVar.setLengthMin}.

        :returns: The length min value
        :rtype: number | null

        Returns minimum length assigned to the interval variable during its
        construction by :meth:`Model.interval_var` or later by
        function :meth:`IntervalVar.set_length` or function :meth:`IntervalVar.set_length_min`.

        If the interval is absent, the function returns `null`.

        **Note:** This function returns the minimum length of the interval in the
        model (before the solve), not in the solution.
        """
        if self.is_absent():
            return None
        return self._props.get('lengthMin', 0)

    def get_length_max(self) -> int | None:
        r"""
        Returns the maximum length assigned to the interval variable during its construction by {@meth Model.intervalVar} or later by function {@meth IntervalVar.setLength} or function {@meth IntervalVar.setLengthMax}.

        :returns: The length max value
        :rtype: number | null

        Returns the maximum length assigned to the interval variable during its
        construction by :meth:`Model.interval_var` or later by
        function :meth:`IntervalVar.set_length` or function :meth:`IntervalVar.set_length_max`.

        If the interval is absent, the function returns `null`.

        **Note:** This function returns the maximum length of the interval in the
        model (before the solve), not in the solution.
        """
        if self.is_absent():
            return None
        return self._props.get('lengthMax', LengthMax)

    # Modifiers
    def make_optional(self) -> None:
        r"""
        Makes the interval variable optional.

        :returns: Returns the interval variable itself to allow chaining.
        :rtype: IntervalVar

        Optional interval variable can be *absent* in the solution i.e. can be omitted.

        It is equivalent to setting `optional: true` in :meth:`Model.interval_var`.

        .. seealso::

            - :meth:`IntervalVar.make_present`, :meth:`IntervalVar.make_absent`.
            - :meth:`IntervalVar.is_optional`, :meth:`IntervalVar.is_present`, :meth:`IntervalVar.is_absent`.
        """
        self._props['status'] = _PresenceStatus.Optional

    def make_present(self) -> None:
        r"""
        Makes the interval variable present.

        :returns: Returns the interval variable itself to allow chaining.
        :rtype: IntervalVar

        The present interval variable cannot be *absent* in the solution, i.e., cannot be omitted.

        It is equivalent to setting `optional: false` in :meth:`Model.interval_var`.

        .. seealso::

            - :meth:`IntervalVar.make_optional`, :meth:`IntervalVar.make_absent`.
            - :meth:`IntervalVar.is_optional`, :meth:`IntervalVar.is_present`, :meth:`IntervalVar.is_absent`.
        """
        self._props.pop('status', None)

    def make_absent(self) -> None:
        r"""
        Makes the interval variable absent.

        :returns: Returns the interval variable itself to allow chaining.
        :rtype: IntervalVar

        Absent interval variable cannot be *present* in the solution, i.e., it will be omitted in the solution (and
        everything that depends on it).

        .. seealso::

            - :meth:`IntervalVar.make_optional`, :meth:`IntervalVar.make_present`.
            - :meth:`IntervalVar.is_optional`, :meth:`IntervalVar.is_present`, :meth:`IntervalVar.is_absent`.
        """
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
        r"""
        Sets the minimum start of the interval variable to the given value.

        :param sMin: The minimum start value to set
        :type sMin: number

        :returns: The interval variable itself (for method chaining)
        :rtype: IntervalVar

        Sets the minimum start of the interval variable to the given value.

        It overwrites any previous minimum start limit given at variable creation by
        :meth:`Model.interval_var` or later by
        :meth:`IntervalVar.set_start` or :meth:`IntervalVar.set_start_min`.
        This function does not change the maximum start.

        Note that the start of the interval variable must be in the range :class:`IntervalMin` to :class:`IntervalMax`.

        .. seealso::

            - :meth:`IntervalVar.set_start`, :meth:`IntervalVar.set_start_max`.
            - :meth:`IntervalVar.get_start_min`, :meth:`IntervalVar.get_start_max`.
        """
        self._props['startMin'] = int(s_min)

    def set_start_max(self, s_max: int) -> None:
        r"""
        Sets the maximum start of the interval variable to the given value.

        :param sMax: The maximum start value to set
        :type sMax: number

        :returns: The interval variable itself (for method chaining)
        :rtype: IntervalVar

        Sets the maximum start of the interval variable to the given value.

        It overwrites any previous maximum start limit given at variable creation by
        :meth:`Model.interval_var` or later by
        :meth:`IntervalVar.set_start` or :meth:`IntervalVar.set_start_max`.
        The minimum start is not changed by this function.

        Note that the start of the interval variable must be in the range :class:`IntervalMin` to :class:`IntervalMax`.

        .. seealso::

            - :meth:`IntervalVar.set_start`, :meth:`IntervalVar.set_start_min`.
            - :meth:`IntervalVar.get_start_min`, :meth:`IntervalVar.get_start_max`.
        """
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
        r"""
        Sets the minimum end of the interval variable to the given value.

        :param eMin: The minimum end value to set
        :type eMin: number

        :returns: The interval variable itself (for method chaining)
        :rtype: IntervalVar

        Sets the minimum end of the interval variable to the given value.

        It overwrites any previous minimum end limit given at variable creation by
        :meth:`Model.interval_var` or later by
        :meth:`IntervalVar.set_end` or :meth:`IntervalVar.set_end_min`.
        This function does not change the maximum end.

        Note that the end of the interval variable must be in the range :class:`IntervalMin` to :class:`IntervalMax`.

        .. seealso::

            - :meth:`IntervalVar.set_end`, :meth:`IntervalVar.set_end_max`.
            - :meth:`IntervalVar.get_end_min`, :meth:`IntervalVar.get_end_max`.
        """
        self._props['endMin'] = int(e_min)

    def set_end_max(self, e_max: int) -> None:
        r"""
        Sets the maximum end of the interval variable to the given value.

        :param eMax: The maximum end value to set
        :type eMax: number

        :returns: The interval variable itself (for method chaining)
        :rtype: IntervalVar

        Sets the maximum end of the interval variable to the given value.
        It overwrites any previous maximum end limit given at variable creation by
        :meth:`Model.interval_var` or later by
        :meth:`IntervalVar.set_end` or :meth:`IntervalVar.set_end_max`.
        This function does not change the minimum end.

        Note that the end of the interval variable must be in the range :class:`IntervalMin` to :class:`IntervalMax`.

        .. seealso::

            - :meth:`IntervalVar.set_end`, :meth:`IntervalVar.set_end_min`.
            - :meth:`IntervalVar.get_end_min`, :meth:`IntervalVar.get_end_max`.
        """
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
        r"""
        Sets the minimum length of the interval variable to the given value.

        :param lMin: The minimum length value to set
        :type lMin: number

        :returns: The interval variable itself (for method chaining)
        :rtype: IntervalVar

        Sets the minimum length of the interval variable to the given value.
        It overwrites any previous minimum length limit given at variable creation by
        :meth:`Model.interval_var` or later by
        :meth:`IntervalVar.set_length` or :meth:`IntervalVar.set_length_min`.
        This function does not change the maximum length.

        Note that the length of the interval variable must be in the range 0 to :class:`LengthMax`.

        .. seealso::

            - :meth:`IntervalVar.set_length`, :meth:`IntervalVar.set_length_max`.
            - :meth:`IntervalVar.get_length_min`, :meth:`IntervalVar.get_length_max`.
        """
        self._props['lengthMin'] = int(l_min)

    def set_length_max(self, l_max: int) -> None:
        r"""
        Sets the maximum length of the interval variable to the given value.

        :param lMax: The maximum length value to set
        :type lMax: number

        :returns: The interval variable itself (for method chaining)
        :rtype: IntervalVar

        Sets the maximum length of the interval variable to the given value.
        It overwrites any previous maximum length limit given at variable creation by
        :meth:`Model.interval_var` or later by
        :meth:`IntervalVar.set_length` or :meth:`IntervalVar.set_length_max`.
        This function does not change the minimum length.

        Note that the length of the interval must not exceed :class:`LengthMax`.

        .. seealso::

            - :meth:`IntervalVar.set_length`, :meth:`IntervalVar.set_length_min`.
            - :meth:`IntervalVar.get_length_min`, :meth:`IntervalVar.get_length_max`.
        """
        self._props['lengthMax'] = int(l_max)
