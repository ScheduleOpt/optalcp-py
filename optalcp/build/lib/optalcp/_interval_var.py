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
    """
    Interval variable is a task, action, operation, or any other interval with a start
    and an end. The start and the end of the interval are unknowns that the solver
    has to find. They could be accessed as integer expressions using
    :meth:`IntervalVar.start` and :meth:`IntervalVar.end`.
    or using :meth:`Model.start_of` and :meth:`Model.end_of`.
    In addition to the start and the end of the interval, the interval variable
    has a length (equal to *end - start*) that can be accessed using
    :meth:`IntervalVar.length` or :meth:`Model.length_of`.

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

    def presence(self, ) -> BoolExpr:
        """#doc[IntervalVar.presenceOf]"""
        out_params: list[_Argument] = [self._as_arg()]
        return BoolExpr(self._model, "intervalPresenceOf", out_params)

    def start(self, ) -> IntExpr:
        """
        :returns: The resulting integer expression
        :rtype: IntExpr

        Returns the start time of the interval variable as an integer expression.

        The start time can be used in constraints or as part of the objective function.

        .. rubric:: Example

        .. code-block:: python

            task = model.interval_var(name="task")
            value = task.start()

            # Alternative: using Model method
            value2 = model.start_of(task)
        """
        out_params: list[_Argument] = [self._as_arg()]
        return IntExpr(self._model, "startOf", out_params)

    def end(self, ) -> IntExpr:
        """
        :returns: The resulting integer expression
        :rtype: IntExpr

        Returns the end time of the interval variable as an integer expression.

        The end time can be used in constraints or as part of the objective function.

        .. rubric:: Example

        .. code-block:: python

            task = model.interval_var(name="task")
            value = task.end()

            # Alternative: using Model method
            value2 = model.end_of(task)
        """
        out_params: list[_Argument] = [self._as_arg()]
        return IntExpr(self._model, "endOf", out_params)

    def length(self, ) -> IntExpr:
        """
        :returns: The resulting integer expression
        :rtype: IntExpr

        Returns the length of the interval variable as an integer expression.

        The length can be used in constraints or as part of the objective function.

        .. rubric:: Example

        .. code-block:: python

            task = model.interval_var(name="task")
            value = task.length()

            # Alternative: using Model method
            value2 = model.length_of(task)
        """
        out_params: list[_Argument] = [self._as_arg()]
        return IntExpr(self._model, "lengthOf", out_params)

    def start_or(self, absentValue: int | bool) -> IntExpr:
        """#doc[IntervalVar.startOr]"""
        out_params: list[_Argument] = [self._as_arg(), _wrap_int(absentValue)]
        return IntExpr(self._model, "startOr", out_params)

    def end_or(self, absentValue: int | bool) -> IntExpr:
        """#doc[IntervalVar.endOr]"""
        out_params: list[_Argument] = [self._as_arg(), _wrap_int(absentValue)]
        return IntExpr(self._model, "endOr", out_params)

    def length_or(self, absentValue: int | bool) -> IntExpr:
        """#doc[IntervalVar.lengthOr]"""
        out_params: list[_Argument] = [self._as_arg(), _wrap_int(absentValue)]
        return IntExpr(self._model, "lengthOr", out_params)

    def _alternative_cost(self, options: Iterable[IntervalVar], weights: Iterable[int | bool]) -> IntExpr:
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap_list(options), _wrap_int_list(weights)]
        return IntExpr(self._model, "intAlternativeCost", out_params)

    def end_before_end(self, successor: IntervalVar, delay: IntExpr | int | bool = 0) -> Constraint:
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """#doc[IntervalVar.position]"""
        out_params: list[_Argument] = [self._as_arg(), SequenceVar._wrap(sequence)]
        return IntExpr(self._model, "position", out_params)

    def pulse(self, height: IntExpr | int | bool) -> CumulExpr:
        """#doc[IntervalVar.pulse]"""
        out_params: list[_Argument] = [self._as_arg(), IntExpr._wrap(height)]
        return CumulExpr(self._model, "pulse", out_params)

    def step_at_start(self, height: IntExpr | int | bool) -> CumulExpr:
        """#doc[IntervalVar.stepAtStart]"""
        out_params: list[_Argument] = [self._as_arg(), IntExpr._wrap(height)]
        return CumulExpr(self._model, "stepAtStart", out_params)

    def step_at_end(self, height: IntExpr | int | bool) -> CumulExpr:
        """#doc[IntervalVar.stepAtEnd]"""
        out_params: list[_Argument] = [self._as_arg(), IntExpr._wrap(height)]
        return CumulExpr(self._model, "stepAtEnd", out_params)

    def _precedence_energy_before(self, others: Iterable[IntervalVar], heights: Iterable[int | bool], capacity: int | bool) -> Constraint:
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap_list(others), _wrap_int_list(heights), _wrap_int(capacity)]
        return Constraint(self._model, "precedenceEnergyBefore", out_params)

    def _precedence_energy_after(self, others: Iterable[IntervalVar], heights: Iterable[int | bool], capacity: int | bool) -> Constraint:
        out_params: list[_Argument] = [self._as_arg(), IntervalVar._wrap_list(others), _wrap_int_list(heights), _wrap_int(capacity)]
        return Constraint(self._model, "precedenceEnergyAfter", out_params)

    def forbid_extent(self, func: IntStepFunction) -> Constraint:
        """
        This function prevents the specified interval variable from overlapping with segments of the step function where the value is zero. the value is zero.

        :param func: The step function.
        :type func: IntStepFunction

        :returns: The constraint forbidding the extent (entire interval).
        :rtype: Constraint

        This function prevents the specified interval variable from overlapping with segments of the step function where the value is zero. I.e., if $[s, e)$ is a segment of the step function where the value is zero, then the interval variable either ends before $s$ ($\mathtt{interval.end()} \le s$) or starts after $e$ ($e \le \mathtt{interval.start()}$).

        .. seealso::

            - :meth:`Model.forbid_extent` for the equivalent function on :class:`Model`.
            - :meth:`Model.forbid_start`, :meth:`Model.forbid_end` for similar functions that constrain the start/end of an interval variable.
            - :meth:`Model.step_function_eval` for evaluation of a step function.
        """
        out_params: list[_Argument] = [self._as_arg(), IntStepFunction._wrap(func)]
        return Constraint(self._model, "forbidExtent", out_params)

    def forbid_start(self, func: IntStepFunction) -> Constraint:
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
        """
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
