"""
Core model classes for OptalCP Python API.
"""

from __future__ import annotations
from collections.abc import Iterable
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ._result import SolveResult
    from ._solution import Solution
from ._expressions import (
    # Constants
    IntVarMax,
    IntVarMin,
    # Expression classes
    Constraint,
    IntExpr,
    BoolExpr,
    CumulExpr,
    Directive,
    _SearchDecision,
    # Internal types
    _ElementProps,
    _Argument,
    _wrap_int,
    _wrap_int_list,
    _wrap_bool,
)
from ._int_bool_var import IntVar, BoolVar
from ._scheduling import IntervalVar, SequenceVar, IntStepFunction
from ._parameters import Parameters
from ._constants import _PresenceStatus


class Model:
    r"""
    *Model* captures the problem to be solved. It contains variables,
    constraints and objective function.

    To create an optimization model, you must first create a *Model* object.
    Then you can use the methods of the *Model* to create variables (e.g. :meth:`Model.interval_var`), the objective function (:meth:`Model.minimize` or :meth:`Model.maximize`)
    and constraints (e.g. :meth:`Model.constraint` or :meth:`Model.no_overlap`).
    Note that a boolean expression becomes a constraint only by passing it to
    the function :meth:`Model.constraint`; otherwise, it is not enforced.

    To solve a model, pass it to function :func:`solve` or to :class:`Solver`
    class.

    ### Available modeling elements

    #### Variables

    Interval variables can be created by function :meth:`Model.interval_var`, integer variables by function :meth:`Model.int_var`.

    #### Basic integer expressions

    * :meth:`Model.start`: start of an interval variable (optional integer expression).
    * :meth:`Model.start_or_else`: start of an interval variable or a constant when it is *absent*.
    * :meth:`Model.end`:   end of an interval variable (optional integer expression).
    * :meth:`Model.end_or_else`:   end of an interval variable or a constant when it is *absent*.
    * :meth:`Model.length`: length of an interval variable (optional integer expression).
    * :meth:`Model.length_or_else`: length of an interval variable or a constant when it is *absent*.
    * :meth:`Model.guard`: replaces *absent* value by a constant.

    #### Integer arithmetics

    * :meth:`Model.plus`:  addition.
    * :meth:`Model.minus`: subtraction.
    * :meth:`Model.neg`:   negation (changes sign).
    * :meth:`Model.times`: multiplication.
    * :meth:`Model.div`:   division (rounds to zero).
    * :meth:`Model.abs`:   absolute value.
    * :meth:`Model.min2`:  minimum of two integer expressions.
    * :meth:`Model.min`:   minimum of an array of integer expressions.
    * :meth:`Model.max2`:  maximum of two integer expressions.
    * :meth:`Model.max`:   maximum of an array of integer expressions.
    * :meth:`Model.sum`:   sum of an array of integer expressions.

    #### Comparison operators for integer expressions

    * :meth:`Model.eq`: equality.
    * :meth:`Model.ne`: inequality.
    * :meth:`Model.lt`: less than.
    * :meth:`Model.le`: less than or equal to.
    * :meth:`Model.gt`: greater than.
    * :meth:`Model.ge`: greater than or equal to.
    * :meth:`Model.identity`: constraints two integer expressions to be equal, including the presence status.

    #### Boolean operators

    * :meth:`Model.not_`: negation.
    * :meth:`Model.and_`: conjunction.
    * :meth:`Model.or_`:  disjunction.
    * :meth:`Model.implies`: implication.

    #### Functions returning :class:`BoolExpr`

    * :meth:`Model.presence_of`: whether the argument is *present* or *absent*.
    * :meth:`Model.in_range`: whether an integer expression is within the given range

    #### Basic constraints on interval variables

    * :meth:`Model.alternative`: an alternative between multiple interval variables.
    * :meth:`Model.span`: span (cover) of interval variables.
    * :meth:`Model.end_before_end`, :meth:`Model.end_before_start`, :meth:`Model.start_before_end`, :meth:`Model.start_before_start`,
    :meth:`Model.end_at_start`, :meth:`Model.start_at_end`: precedence constraints.

    #### Disjunction (noOverlap)

    * :meth:`Model.sequence_var`: sequence variable over a set of interval variables.
    * :meth:`Model.no_overlap`: constraints a set of interval variables to not overlap (possibly with transition times).
    * :meth:`Model.position`: returns the position of an interval variable in a sequence.

    #### Basic cumulative expressions

    * :meth:`Model.pulse`: changes value during the interval variable.
    * :meth:`Model.step_at_start`: changes value at the start of the interval variable.
    * :meth:`Model.step_at_end`: changes value at the end of the interval variable.
    * :meth:`Model.step_at`: changes value at a given time.

    #### Combining cumulative expressions

    * :meth:`Model.cumul_neg`: negation.
    * :meth:`Model.cumul_plus`: addition.
    * :meth:`Model.cumul_minus`: subtraction.
    * :meth:`Model.cumul_sum`: sum of multiple expressions.

    #### Constraints on cumulative expressions

    * :meth:`Model.cumul_ge`: greater than or equal to a constant.
    * :meth:`Model.cumul_le`: less than or equal to a constant.

    #### Mapping/batching

    * :meth:`Model.itv_mapping`: map tasks (interval variables) to slots (other interval variables).

    #### Constraints on integer variables/expressions

    * :meth:`Model.pack`: pack items of various sizes into a set of bins.

    #### Objective

    * :meth:`Model.minimize`: minimize an integer expression.
    * :meth:`Model.maximize`: maximize an integer expression.

    Our goal is to schedule a set of tasks such that it is finished as soon as
    possible (i.e., the makespan is minimized).  Each task has a fixed duration, and
    cannot be interrupted.  Moreover, each task needs a certain number of
    workers to be executed, and the total number of workers is limited.
    The input data are generated randomly.

    .. seealso::

        - :func:`solve`.
        - :class:`Solution`.
        - :class:`Solver`.
    """

    def __init__(self, *, name: str | None = None):
        # TODO-MISSING-DOC-FILE: Constructor params not documented in Model.md
        """
        Create a new empty model.

        Args:
            name: Optional name for the model (useful for debugging and benchmarking)
        """
        self._name = name
        self._model: list[_Argument] = []  # Top-level constraints
        self._refs: list[_ElementProps] = []  # Nodes referenced by ID
        self._objective: _ElementProps | None = None
        self._interval_vars: list[IntervalVar] = []
        self._int_vars: list[IntVar] = []
        self._bool_vars: list[BoolVar] = []

    # TODO-MISSING-DOC-FILE: Python uses @property, JS uses getName()/setName() methods
    @property
    def name(self) -> str | None:
        """
        The name of the model.

        The name is optional and primarily useful for debugging and benchmarking purposes.
        When set, it helps identify the model in logs and benchmark results.

        Returns:
            The name of the model, or None if no name was set
        """
        return self._name

    @name.setter
    def name(self, value: str | None) -> None:
        """
        Set the name of the model.

        Args:
            value: The new name for the model, or None to clear the name
        """
        if value is not None and not isinstance(value, str):
            raise TypeError(f"Model name must be str or None, got {type(value).__name__}")
        self._name = value

    def get_interval_vars(self) -> list[IntervalVar]:
        """
        Return a list of all interval variables in the model.

        Returns:
            A copy of the list of interval variables
        """
        return list(self._interval_vars)

    def get_int_vars(self) -> list[IntVar]:
        """
        Return a list of all integer variables in the model.

        Returns:
            A copy of the list of integer variables
        """
        return list(self._int_vars)

    def get_bool_vars(self) -> list[BoolVar]:
        """
        Return a list of all boolean variables in the model.

        Returns:
            A copy of the list of boolean variables
        """
        return list(self._bool_vars)

    def interval_var(self,
                     start: tuple[int, int] | None = None,
                     end: tuple[int, int] | None = None,
                     length: int | tuple[int, int] | None = None,
                     optional: bool = False,
                     name: str | None = None) -> IntervalVar:
        r"""
        Creates a new interval variable and adds it to the model.

        :param params: Interval variable parameters with optional properties for start, end, length, optional, and name
        :type params: object

        :returns: The created interval variable.
        :rtype: IntervalVar

        An interval variable represents an unknown interval (a task, operation,
        action) that the solver assigns a value in such a way as to satisfy all
        constraints.  An interval variable has a start, end, and length. In a
        solution, *start ≤ end* and  *length = end - start*.

        The interval variable can be optional. In this case, its value in a solution
        could be *absent*, meaning that the task/operation is not performed.

        Parameters `params.start`, `params.end`, and `params.length` can be either a
        number or a tuple of two numbers.  If a number is given, it represents a
        fixed value. If a tuple is given, it represents a range of possible values.
        The default range for start, end and length is `0` to `IntervalMax`.
        If a range is specified but one of the values is undefined (e.g. `start: [, 100]`)
        then the default value is used instead (in our case `0`).

        .. seealso::

            - :class:`IntervalVar`.
        """
        props: _ElementProps = {
            'func': 'intervalVar',
            'args': []
        }

        if name:
            props['name'] = name

        if optional:
            props['status'] = _PresenceStatus.Optional

        if start is not None:
            props['startMin'] = start[0]
            props['startMax'] = start[1]

        if end is not None:
            props['endMin'] = end[0]
            props['endMax'] = end[1]

        if length is not None:
            if isinstance(length, int):
                props['lengthMin'] = length
                props['lengthMax'] = length
            else:
                props['lengthMin'] = length[0]
                props['lengthMax'] = length[1]

        var = IntervalVar(self, props)
        self._interval_vars.append(var)
        return var

    def int_var(self,
                min: int = IntVarMin,
                max: int = IntVarMax,
                optional: bool = False,
                name: str | None = None) -> IntVar:
        r"""
        Creates a new integer variable and adds it to the model.

        :param params: Integer variable parameters with optional properties for range, optional flag, and name
        :type params: object

        :returns: The created integer variable.
        :rtype: IntVar

        An integer variable represents an unknown value the solver must find.
        The variable can be optional.
        In this case, its value in a solution could be *absent*, meaning that the solution does not use the variable at all.

        The parameter `params.range` can be either a number or a tuple of two numbers.
        If a number is given, it represents a fixed value.
        If a tuple is given, it represents a range of possible values.
        The default range is `0` to `IntVarMax`.
        If a range is specified but one of the values is undefined (e.g., `range: [, 100]`), then the default value is used instead (in our case, `0`).
        """
        props: _ElementProps = {
            'func': 'intVar',
            'args': [],
            'min': min,
            'max': max,
        }

        if optional:
            props['status'] = _PresenceStatus.Optional
        if name:
            props['name'] = name

        var = IntVar(self, props)
        self._int_vars.append(var)
        return var

    # TODO-MISSING-DOC-FILE: Model.boolVar.md needs to be created (currently marked internal in JS but public in Python)
    def bool_var(self, optional: bool = False, name: str | None = None) -> BoolVar:
        """
        Create a boolean variable.

        A boolean variable represents an unknown truth value (True or False) that the
        solver must find. Boolean variables are useful for modeling decisions, choices,
        or logical conditions in your problem.

        Like other variable types in OptalCP, boolean variables can be optional, meaning
        they can be absent in a solution (in addition to being True or False).

        Args:
            name: Optional name for the variable (useful for debugging)

        Returns:
            The new boolean variable

        Examples:
            Create boolean variables to model decisions:

            >>> import optalcp as cp
            >>> model = cp.Model()
            >>> use_machine_A = model.bool_var(name="use_machine_A")
            >>> use_machine_B = model.bool_var(name="use_machine_B")
            >>> # Constraint: must use at least one machine
            >>> model.constraint(use_machine_A | use_machine_B)
            >>> # Constraint: cannot use both machines
            >>> model.constraint(~(use_machine_A & use_machine_B))

        See Also:
            interval_var: The primary variable type for scheduling problems
            int_var: For numeric decisions
        """
        props: _ElementProps = {
            'func': 'boolVar',
            'args': [],
            'min': False,
            'max': True
        }

        if name:
            props['name'] = name
        if optional:
            props['status'] = _PresenceStatus.Optional

        var = BoolVar(self, props)
        self._bool_vars.append(var)
        return var

    def sequence_var(self,
                     intervals: Iterable[IntervalVar],
                     types: Iterable[int] | None = None,
                     name: str | None = None) -> SequenceVar:
        r"""
        Creates a sequence variable from the provided set of interval variables.

        :param intervals: Interval variables that will form the sequence in the solution
        :type intervals: IntervalVar[]
        :param types: Types of the intervals, used in particular for transition times
        :type types: number[]
        :param name: Name assigned to the sequence variable
        :type name: string

        :returns: The created sequence variable
        :rtype: SequenceVar

        Sequence variable is used together with :meth:`SequenceVar.no_overlap`
        constraint to model a set of intervals that cannot overlap and so they form
        a sequence in the solution. Sequence variable allows us to constrain the sequence further.
        For example, by specifying sequence-dependent minimum
        transition times.

        Types can be used to mark intervals with similar properties. In
        particular, they behave similarly in terms of transition times.
        Interval variable `intervals[0]` will have type `type[0]`, `intervals[1]`
        will have type `type[1]` and so on.

        If `types` are not specified then `intervals[0]` will have type 0,
        `intervals[1]` will have type 1, and so on.

        .. seealso::

            - :meth:`SequenceVar.no_overlap` for an example of sequenceVar usage with transition times.
            - :class:`SequenceVar`.
            - :meth:`Model.no_overlap`.
        """
        # Convert interval variables to arguments
        interval_args = IntervalVar._wrap_list(intervals)

        # Build the arguments list
        out_params: list[_Argument] = [interval_args]
        if types is not None:
            types_args = _wrap_int_list(types)
            if len(types_args) != len(interval_args):
                raise ValueError(f"Length of types ({len(types_args)}) must equal length of intervals ({len(interval_args)})")
            out_params.append(types_args)

        result = SequenceVar(self, "sequenceVar", out_params)
        if name:
            result.name = name
        self._model.append(result._as_arg())
        return result

    def no_overlap(self,
                   intervals: Iterable[IntervalVar] | SequenceVar,
                   transitions: Iterable[Iterable[int]] | None = None) -> Constraint:
        """#doc[Model.noOverlap]"""
        # If given a SequenceVar, use it directly; otherwise create an auxiliary sequence variable
        if isinstance(intervals, SequenceVar):
            sequence = intervals
        else:
            sequence = self._auxiliary_sequence_var(intervals)

        # Apply the no_overlap constraint on the sequence
        return sequence.no_overlap(transitions)

    def _auxiliary_sequence_var(self, intervals: Iterable[IntervalVar]) -> SequenceVar:
        """
        Internal: Create an auxiliary sequence variable.

        An auxiliary sequence variable is used internally and doesn't appear
        in the model's variable list.
        """
        sequence = self.sequence_var(intervals)
        sequence._make_auxiliary()
        return sequence

    def step_function(self, values: Iterable[tuple[int, int]]) -> IntStepFunction:
        r"""
        Creates a new integer step function.

        :param values: An array of points defining the step function in the form [[x0, y0], [x1, y1], ..., [xn, yn]], where xi and yi are integers. The array must be sorted by xi
        :type values: number[][]

        :returns: The created step function
        :rtype: IntStepFunction

        Integer step function is a piecewise constant function defined on integer
        values in range :class:`IntVarMin` to :class:`IntVarMax`.  The function is
        defined as follows:

        * :math:`f(x) = 0` for :math:`x < x_0`,
        * :math:`f(x) = y_i` for :math:`x_i \leq x < x_{i+1}`
        * :math:`f(x) = y_n` for :math:`x \geq x_n`.

        Step functions can be used in the following ways:

        * Function :meth:`Model.step_function_eval` evaluates the function at the given point (given as :class:`IntExpr`).
        * Function :meth:`Model.step_function_sum` computes a sum (integral) of the function over an :class:`IntervalVar`.
        * Constraints :meth:`Model.forbid_start` and :meth:`Model.forbid_end` forbid the start/end of an :class:`IntervalVar` to be in a zero-value interval of the function.
        * Constraint :meth:`Model.forbid_extent` forbids the extent of an :class:`IntervalVar` to be in a zero-value interval of the function.
        """
        return IntStepFunction(self, values)

    def add(self, constraint: Constraint | BoolExpr | bool | Iterable[Constraint | BoolExpr | bool]) -> None:
        """#doc[Model.add]"""
        if isinstance(constraint, (Constraint, BoolExpr, bool)):
            if isinstance(constraint, Constraint):
                self._model.append(constraint._as_arg())
            else:
                self._model.append(BoolExpr._wrap(constraint))
        else:
            for c in constraint:
                if isinstance(c, Constraint):
                    self._model.append(c._as_arg())
                else:
                    self._model.append(BoolExpr._wrap(c))

    def minimize(self, expr: IntExpr | int) -> None:
        r"""
        Minimize the provided expression to find solution with minimal value.

        :param expr: The expression to minimize
        :type expr: IntExpr

        :rtype: void

        Equivalent of function :meth:`IntExpr.minimize`.

        In the following model, we search for a solution that minimizes the maximum
        end of the two intervals `x` and `y`:

        .. seealso::

            - :meth:`Model.maximize`.
        """
        self._objective = {
            'func': 'minimize',
            'args': [IntExpr._wrap(expr)]
        }

    def maximize(self, expr: IntExpr | int) -> None:
        r"""
        Maximize the provided expression to find solution with maximal value.

        :param expr: The expression to maximize
        :type expr: IntExpr

        :rtype: void

        Equivalent of function :meth:`IntExpr.maximize`.

        In the following model, we search for a solution that maximizes
        the length of the interval variable `x`:

        .. seealso::

            - :meth:`Model.minimize`.
        """
        self._objective = {
            'func': 'maximize',
            'args': [IntExpr._wrap(expr)]
        }

    def _add_constraint(self, constraint: Constraint | BoolExpr) -> None:
        """Internal: Add a constraint to the model."""
        self._model.append(constraint._as_arg())

    def _add_directive(self, directive: Directive) -> None:
        """Internal: Add a directive to the model."""
        self._model.append(directive._as_arg())

    def _get_new_ref_id(self, props: _ElementProps) -> int:
        """Internal: Allocate a new reference ID for a node."""
        ref_id = len(self._refs)
        self._refs.append(props)
        return ref_id

    def _to_dict(self) -> dict[str, Any]:
        """Internal: Convert model to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            'refs': self._refs,
            'model': self._model
        }

        if self._name:
            result['name'] = self._name

        if self._objective:
            result['objective'] = self._objective

        return result

    def _from_dict(self, data: dict[str, Any]) -> None:
        """Internal: Restore model from dictionary created by _to_dict()."""
        # Restore the core model structure
        self._refs = data['refs']
        self._model = data['model']

        # Restore optional fields
        if 'name' in data:
            self._name = data['name']

        if 'objective' in data:
            self._objective = data['objective']

        # Reconstruct variable objects from refs
        for i, props in enumerate(self._refs):
            func = props.get('func')
            if func == 'boolVar':
                self._bool_vars.append(BoolVar(self, props, i))
            elif func == 'intVar':
                self._int_vars.append(IntVar(self, props, i))
            elif func == 'intervalVar':
                self._interval_vars.append(IntervalVar(self, props, i))

    def sum(self, args: Iterable[IntExpr | int | bool] | Iterable[CumulExpr]) -> IntExpr | int | CumulExpr:
        r"""
        Creates in integer expression for the sum of the arguments.

        :param args: Array of integer expressions to sum.
        :type args: IntExpr[]

        :returns: The resulting integer expression
        :rtype: IntExpr

        Absent arguments are ignored (treated as zeros). Therefore, the resulting expression is never *absent*.

        Note that binary function :meth:`Model.plus` handles absent values differently. For example, when `x` is *absent* then: 

        * `plus(x, 3)` is *absent*.
        * `sum([x, 3])` is 3.

        Let's consider a set of optional tasks. Due to limited resources and time, only some of them can be executed. Every task has a profit, and we want to maximize the total profit from the executed tasks.
        """

        # Take the first element to determine the type
        args_iter = iter(args)
        try:
            first = next(args_iter)
        except StopIteration:
            # The array is empty
            # Return 0 as the sum of an empty list. For different handling of empty sum, use Model.cumul_sum().
            return 0

        if isinstance(first, CumulExpr):
            wrapped_args = [CumulExpr._wrap(first)]
            for e in args_iter:
                wrapped_args.append(CumulExpr._wrap(e))  #type: ignore[arg-type]
            return CumulExpr(self, "cumulSum", [wrapped_args])
        else:
            wrapped_args = [IntExpr._wrap(first)]
            for e in args_iter:
                wrapped_args.append(IntExpr._wrap(e))  # type: ignore[arg-type]
            return IntExpr(self, "intSum", [wrapped_args])

    def presence_of(self, arg: IntExpr | int | bool | IntervalVar) -> BoolExpr:
        r"""
        Creates a boolean expression that is true if the given argument is present in the solution.

        :param arg: The argument to check for presence in the solution
        :type arg: IntervalVar | IntExpr | int | bool

        :returns: A boolean expression that is true if the argument is present in the solution.
        :rtype: BoolExpr

        The value of the expression remains unknown until a solution is found.
        The expression can be used in a constraint to restrict possible solutions.

        The function is equivalent to :meth:`IntervalVar.presence`
        and :meth:`IntExpr.presence`.

        In the following example, interval variables `x` and `y` must have the same presence status.
        I.e. they must either be both *present* or both *absent*.

        #### Simple constraints over presence

        The solver treats binary constraints over presence in a special way: it
        uses them to better propagate other constraints over the same pairs of variables.
        Let's extend the previous example by a constraint that `x` must end before
        `y` starts:

        In this example, the solver sees (propagates) that the minimum start time of
        `y` is 10 and maximum end time of `x` is 90.  Without the constraint over
        `presence_of`, the solver could not propagate that because one
        of the intervals can be *absent* and the other one *present* (and so the
        value of `isBefore` would be *absent* and the constraint would be
        satisfied).

        To achieve good propagation, it is recommended to use binary
        constraints over `presence_of` when possible. For example, multiple binary
        constraints can be used instead of a single complicated constraint.
        """
        if isinstance(arg, IntervalVar):
            return BoolExpr(self, "intervalPresenceOf", [IntervalVar._wrap(arg)])
        return BoolExpr(self, "intPresenceOf", [IntExpr._wrap(arg)])

    # =========================================================================
    # Solving and serialization methods
    # =========================================================================

    def solve(self,
              params: Parameters | None = None,
              warm_start: "Solution | None" = None) -> "SolveResult":
        r"""
        Solves the model and returns the result.

        :param params: The parameters for solving
        :type params: Parameters
        :param warm_start: The solution to start with
        :type warm_start: Solution

        :returns: The result of the solve.
        :rtype: SolveResult

        Solves the model using the OptalCP solver and returns the result. This is the
        main entry point for solving constraint programming models.

        The solver searches for solutions that satisfy all constraints in the model.
        If an objective was specified (using :meth:`Model.minimize` or
        :meth:`Model.maximize`), the solver searches for optimal or near-optimal
        solutions within the given time limit.

        The returned :class:`SolveResult` contains:

        * `solution` - The best solution found, or `None` if no solution was found.
          Use this to query variable values via methods like `get_start()`, `get_end()`,
          and `get_value()`.
        * `objective_value` - The objective value of the best solution (if an objective
          was specified).
        * `nb_solutions` - The total number of solutions found during the search.
        * `proof` - Whether the solver proved optimality or infeasibility.
        * `duration` - The total time spent solving.
        * Statistics like `nb_branches`, `nb_fails`, and `nb_restarts`.

        When an error occurs (e.g., invalid model, solver not found), the function
        raises an exception.

        ### Parameters

        Solver behavior can be controlled via the `params` argument. Common parameters
        include:

        * `timeLimit` - Maximum solving time in seconds.
        * `solutionLimit` - Stop after finding this many solutions.
        * `nbWorkers` - Number of parallel threads to use.
        * `searchType` - Search strategy (`"LNS"`, `"FDS"`, etc.).

        See :class:`Parameters` for the complete list.

        ### Warm start

        If the `warm_start` parameter is specified, the solver will start with the
        given solution. The solution must be compatible with the model; otherwise,
        an error will be raised. The solver will take advantage of the
        solution to speed up the search: it will search only for better solutions
        (if it is a minimization or maximization problem). The solver may also try to
        improve the provided solution by Large Neighborhood Search.

        ### Advanced usage

        This is a simple blocking function for basic usage. For advanced features
        like event callbacks, progress monitoring, or async support, use the
        :class:`Solver` class instead.

        This method works seamlessly in both regular Python scripts and Jupyter
        notebooks. In Jupyter (where an event loop is already running), it
        automatically handles nested event loops.

        .. rubric:: Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.interval_var(length=10, name="task_x")
            y = model.interval_var(length=20, name="task_y")
            x.end_before_start(y)
            model.minimize(y.end())

            # Basic solve
            result = model.solve()
            print(f"Objective: {result.objective_value}")

            # Solve with parameters
            params = cp.Parameters(timeLimit=60, searchType="LNS")
            result = model.solve(params)

            # Solve with warm start
            if result.solution:
                result2 = model.solve(params, warm_start=result.solution)

        .. seealso::

            - :class:`Solver` for async solving with event callbacks.
            - :class:`Parameters` for available solver parameters.
            - :class:`SolveResult` for the result structure.
            - :class:`Solution` for working with solutions.
        """
        from ._solver import Solver
        return Solver()._sync_solve(self, params, warm_start)

    def to_json(self,
                params: Parameters | None = None,
                warm_start: "Solution | None" = None) -> str:
        r"""
        Exports the model to JSON format.

        :param params: Optional solver parameters to include
        :type params: Parameters
        :param warm_start: Optional initial solution to include
        :type warm_start: Solution

        :returns: A string containing the model in JSON format.
        :rtype: string

        The result can be stored in a file for later use. The model can be
        converted back from JSON format using :meth:`from_json`.

        .. rubric:: Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.interval_var(length=10, name="task_x")
            y = model.interval_var(length=20, name="task_y")
            x.end_before_start(y)
            model.minimize(y.end())

            # Export to JSON
            json_str = model.to_json()

            # Save to file
            with open("model.json", "w") as f:
                f.write(json_str)

            # Later, load from JSON
            model2, params2, warm_start2 = cp.Model.from_json(json_str)

        .. seealso::

            - :meth:`from_json` to import from JSON.
            - :meth:`to_txt` to export as text format.
            - :meth:`to_js` to export as JavaScript code.
        """
        from ._result import _to_json_impl
        return _to_json_impl(self, params, warm_start)

    def to_txt(self,
               params: Parameters | None = None,
               warm_start: "Solution | None" = None) -> str:
        r"""
        Converts the model to text format similar to IBM CP Optimizer file format.

        :param params: Optional solver parameters (mostly unused)
        :type params: Parameters
        :param warm_start: Optional initial solution to include
        :type warm_start: Solution

        :returns: Text representation of the model.
        :rtype: string

        The output is human-readable and can be stored in a file. Unlike JSON format,
        there is no way to convert the text format back into a Model.

        The result is so similar to the file format used by IBM CP Optimizer that,
        under some circumstances, the result can be used as an input file for
        CP Optimizer. However, some differences between OptalCP and CP Optimizer
        make it impossible to guarantee the result is always valid for CP Optimizer.

        Known issues:

        * OptalCP supports optional integer expressions, while CP Optimizer does not.
          If the model contains optional integer expressions, the result will not be
          valid for CP Optimizer or may be badly interpreted. For example, to get
          a valid CP Optimizer file, don't use `interval.start()`, use
          `interval.start_or(default)` instead.
        * For the same reason, prefer precedence constraints such as
          `end_before_start()` over `model.constraint(x.end() <= y.start())`.
        * Negative heights in cumulative expressions (e.g., in `step_at_start()`)
          are not supported by CP Optimizer.

        .. rubric:: Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.interval_var(length=10, name="task_x")
            y = model.interval_var(length=20, name="task_y")
            x.end_before_start(y)
            model.minimize(y.end())

            # Convert to text format
            text = model.to_txt()
            print(text)

            # Save to file
            with open("model.txt", "w") as f:
                f.write(text)

        .. seealso::

            - :meth:`to_js` to export as JavaScript code.
            - :meth:`to_json` to export as JSON (can be imported back).
        """
        from ._solver import Solver
        solver = Solver()
        return solver._sync_to_text(self, params, warm_start)

    def to_js(self,
              params: Parameters | None = None,
              warm_start: "Solution | None" = None) -> str:
        r"""
        Converts the model to equivalent JavaScript code.

        :param params: Optional solver parameters (included in generated code)
        :type params: Parameters
        :param warm_start: Optional initial solution to include
        :type warm_start: Solution

        :returns: JavaScript code representing the model.
        :rtype: string

        The output is human-readable, executable with Node.js, and can be stored
        in a file. It is meant as a way to export a model to a format that is
        executable, human-readable, editable, and independent of other libraries.

        This feature is experimental and the result is not guaranteed to be valid
        in all cases.

        .. rubric:: Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.interval_var(length=10, name="task_x")
            y = model.interval_var(length=20, name="task_y")
            x.end_before_start(y)
            model.minimize(y.end())

            # Convert to JavaScript code
            js_code = model.to_js()
            print(js_code)

            # Save to file
            with open("model.js", "w") as f:
                f.write(js_code)

        .. seealso::

            - :meth:`to_txt` to export as text format.
            - :meth:`to_json` to export as JSON (can be imported back).
        """
        from ._solver import Solver
        solver = Solver()
        return solver._sync_to_js(self, params, warm_start)

    @classmethod
    def from_json(cls, json_str: str) -> "tuple[Model, Parameters | None, Solution | None]":
        r"""
        Creates a model from JSON format.

        :param json_str: A string containing the model in JSON format
        :type json_str: string

        :returns: A tuple containing the model, optional parameters, and optional warm start solution.
        :rtype: tuple[Model, Parameters | None, Solution | None]

        Creates a new Model instance from a JSON string that was previously
        exported using :meth:`to_json`.

        The method returns a tuple with three elements:
        1. The reconstructed Model
        2. Parameters (if they were included in the JSON), or None
        3. Warm start Solution (if it was included in the JSON), or None

        Variables in the new model can be accessed using methods like
        :meth:`Model.get_interval_vars`, :meth:`Model.get_int_vars`, etc.

        .. rubric:: Example

        .. code-block:: python

            import optalcp as cp

            # Create and export a model
            model = cp.Model()
            x = model.interval_var(length=10, name="task_x")
            model.minimize(x.end())

            params = cp.Parameters(timeLimit=60000)
            json_str = model.to_json(params)

            # Save to file
            with open("model.json", "w") as f:
                f.write(json_str)

            # Later, load from file
            with open("model.json", "r") as f:
                json_str = f.read()

            # Restore model, parameters, and warm start
            model2, params2, warm_start2 = cp.Model.from_json(json_str)

            # Access variables
            interval_vars = model2.get_interval_vars()
            print(f"Loaded model with {len(interval_vars)} interval variables")

            # Solve with restored parameters
            if params2:
                result = model2.solve(params2)
            else:
                result = model2.solve()

        .. seealso::

            - :meth:`to_json` to export to JSON.
        """
        from ._result import _from_json_impl
        return _from_json_impl(json_str)

    def _reusable_bool_expr(self, value: BoolExpr | bool) -> BoolExpr:
        out_params: list[_Argument] = [BoolExpr._wrap(value)]
        return BoolExpr(self, "reusableBoolExpr", out_params)

    def _reusable_int_expr(self, value: IntExpr | int | bool) -> IntExpr:
        out_params: list[_Argument] = [IntExpr._wrap(value)]
        return IntExpr(self, "reusableIntExpr", out_params)

    def not_(self, arg: BoolExpr | bool) -> BoolExpr:
        r"""
        Negation of the boolean expression `arg`.

        :param arg: The boolean expression to negate.
        :type arg: BoolExpr

        :returns: The resulting Boolean expression
        :rtype: BoolExpr

        If the argument has value *absent* then the resulting expression has also value *absent*.

        Same as :meth:`BoolExpr.not_`.
        """
        out_params: list[_Argument] = [BoolExpr._wrap(arg)]
        return BoolExpr(self, "boolNot", out_params)

    def or_(self, arg1: BoolExpr | bool, arg2: BoolExpr | bool) -> BoolExpr:
        r"""
        Logical _OR_ of boolean expressions `arg1` and `arg2`.

        :param arg1: The first boolean expression.
        :type arg1: BoolExpr
        :param arg2: The second boolean expression.
        :type arg2: BoolExpr

        :returns: The resulting Boolean expression
        :rtype: BoolExpr

        If one of the arguments has value *absent*, then the resulting expression also has value *absent*.

        Same as :meth:`BoolExpr.or_`.
        """
        out_params: list[_Argument] = [BoolExpr._wrap(arg1), BoolExpr._wrap(arg2)]
        return BoolExpr(self, "boolOr", out_params)

    def and_(self, arg1: BoolExpr | bool, arg2: BoolExpr | bool) -> BoolExpr:
        r"""
        Logical _AND_ of boolean expressions `arg1` and `arg2`.

        :param arg1: The first boolean expression.
        :type arg1: BoolExpr
        :param arg2: The second boolean expression.
        :type arg2: BoolExpr

        :returns: The resulting Boolean expression
        :rtype: BoolExpr

        If one of the arguments has value *absent*, then the resulting expression also has value *absent*.

        Same as :meth:`BoolExpr.and_`.
        """
        out_params: list[_Argument] = [BoolExpr._wrap(arg1), BoolExpr._wrap(arg2)]
        return BoolExpr(self, "boolAnd", out_params)

    def implies(self, arg1: BoolExpr | bool, arg2: BoolExpr | bool) -> BoolExpr:
        r"""
        Logical implication of two boolean expressions, that is `arg1` implies `arg2`.

        :param arg1: The first boolean expression.
        :type arg1: BoolExpr
        :param arg2: The second boolean expression.
        :type arg2: BoolExpr

        :returns: The resulting Boolean expression
        :rtype: BoolExpr

        If one of the arguments has value *absent*, then the resulting expression also has value *absent*.

        Same as :meth:`BoolExpr.implies`.
        """
        out_params: list[_Argument] = [BoolExpr._wrap(arg1), BoolExpr._wrap(arg2)]
        return BoolExpr(self, "boolImplies", out_params)

    def _eq(self, arg1: BoolExpr | bool, arg2: BoolExpr | bool) -> BoolExpr:
        out_params: list[_Argument] = [BoolExpr._wrap(arg1), BoolExpr._wrap(arg2)]
        return BoolExpr(self, "boolEq", out_params)

    def _ne(self, arg1: BoolExpr | bool, arg2: BoolExpr | bool) -> BoolExpr:
        out_params: list[_Argument] = [BoolExpr._wrap(arg1), BoolExpr._wrap(arg2)]
        return BoolExpr(self, "boolNe", out_params)

    def _nand(self, arg1: BoolExpr | bool, arg2: BoolExpr | bool) -> BoolExpr:
        out_params: list[_Argument] = [BoolExpr._wrap(arg1), BoolExpr._wrap(arg2)]
        return BoolExpr(self, "boolNand", out_params)

    def guard(self, arg: IntExpr | int | bool, absentValue: int | bool = 0) -> IntExpr:
        r"""
        Creates an expression that replaces value _absent_ by a constant.

        :param arg: The integer expression to guard.
        :type arg: IntExpr
        :param absentValue: The value to use when the expression is absent.
        :type absentValue: int

        :returns: The resulting integer expression
        :rtype: IntExpr

        The resulting expression is:

        * equal to `arg` if `arg` is *present*
        * and equal to `absentValue` otherwise (i.e. when `arg` is *absent*).

        The default value of `absentValue` is 0.

        The resulting expression is never *absent*.

        Same as :meth:`IntExpr.guard`.
        """
        out_params: list[_Argument] = [IntExpr._wrap(arg), _wrap_int(absentValue)]
        return IntExpr(self, "intGuard", out_params)

    def identity(self, arg1: IntExpr | int | bool, arg2: IntExpr | int | bool) -> Constraint:
        r"""
        Constraints `arg1` and `arg2` to be identical, including their presence status.

        :param arg1: The first integer expression.
        :type arg1: IntExpr
        :param arg2: The second integer expression.
        :type arg2: IntExpr

        :returns: The identity constraint.
        :rtype: Constraint

        Identity is different than equality. For example, if `x` is *absent*, then `eq(x, 0)` is *absent*, but `identity(x, 0)` is *false*.

        Same as :meth:`IntExpr.identity`.
        """
        out_params: list[_Argument] = [IntExpr._wrap(arg1), IntExpr._wrap(arg2)]
        return Constraint(self, "intIdentity", out_params)

    def in_range(self, arg: IntExpr | int | bool, lb: int | bool, ub: int | bool) -> BoolExpr:
        r"""
        Creates Boolean expression `lb` &le; `arg` &le; `ub`.

        :param arg: The integer expression to check.
        :type arg: IntExpr
        :param lb: The lower bound of the range.
        :type lb: int
        :param ub: The upper bound of the range.
        :type ub: int

        :returns: The resulting Boolean expression
        :rtype: BoolExpr

        If `arg` has value *absent* then the resulting expression has also value *absent*.

        Use function :meth:`Model.constraint` to create a constraint from this expression.

        Same as :meth:`IntExpr.inRange`.
        """
        out_params: list[_Argument] = [IntExpr._wrap(arg), _wrap_int(lb), _wrap_int(ub)]
        return BoolExpr(self, "intInRange", out_params)

    def _not_in_range(self, arg: IntExpr | int | bool, lb: int | bool, ub: int | bool) -> BoolExpr:
        out_params: list[_Argument] = [IntExpr._wrap(arg), _wrap_int(lb), _wrap_int(ub)]
        return BoolExpr(self, "intNotInRange", out_params)

    def abs(self, arg: IntExpr | int | bool) -> IntExpr:
        r"""
        Creates an integer expression which is absolute value of `arg`.

        :param arg: The integer expression.
        :type arg: IntExpr

        :returns: The resulting integer expression
        :rtype: IntExpr

        If `arg` has value *absent* then the resulting expression has also value *absent*.

        Same as :meth:`IntExpr.abs`.
        """
        out_params: list[_Argument] = [IntExpr._wrap(arg)]
        return IntExpr(self, "intAbs", out_params)

    def min2(self, arg1: IntExpr | int | bool, arg2: IntExpr | int | bool) -> IntExpr:
        r"""
        Creates an integer expression which is the minimum of `arg1` and `arg2`.

        :param arg1: The first integer expression.
        :type arg1: IntExpr
        :param arg2: The second integer expression.
        :type arg2: IntExpr

        :returns: The resulting integer expression
        :rtype: IntExpr

        If one of the arguments has value *absent*, then the resulting expression also has value *absent*.

        Same as :meth:`IntExpr.min2`. See :meth:`Model.min` for n-ary minimum.
        """
        out_params: list[_Argument] = [IntExpr._wrap(arg1), IntExpr._wrap(arg2)]
        return IntExpr(self, "intMin2", out_params)

    def max2(self, arg1: IntExpr | int | bool, arg2: IntExpr | int | bool) -> IntExpr:
        r"""
        Creates an integer expression which is the maximum of `arg1` and `arg2`.

        :param arg1: The first integer expression.
        :type arg1: IntExpr
        :param arg2: The second integer expression.
        :type arg2: IntExpr

        :returns: The resulting integer expression
        :rtype: IntExpr

        If one of the arguments has value *absent*, then the resulting expression also has value *absent*.

        Same as :meth:`IntExpr.max2`. See :meth:`Model.max` for n-ary maximum.
        """
        out_params: list[_Argument] = [IntExpr._wrap(arg1), IntExpr._wrap(arg2)]
        return IntExpr(self, "intMax2", out_params)

    def max(self, args: Iterable[IntExpr | int | bool]) -> IntExpr:
        r"""
        Creates an integer expression for the maximum of the arguments.

        :param args: Array of integer expressions to compute maximum of.
        :type args: IntExpr[]

        :returns: The resulting integer expression
        :rtype: IntExpr

        Absent arguments are ignored as if they were not specified in the input array `args`. Maximum of an empty set (i.e. `max([])` is *absent*. The maximum is *absent* also if all arguments are *absent*.

        Note that binary function :meth:`Model.max2` handles absent values differently. For example, when `x` is *absent* then: 

        * `max2(x, 5)` is *absent*.
        * `max([x, 5])` is 5.
        * `max([x])` is *absent*.

        A common use case is to compute *makespan* of a set of tasks, i.e. the time when the last task finishes. In the following example, we minimize the makespan of a set of tasks (other parts of the model are omitted).

        Notice that when a task is *absent* (not executed), then its end time is *absent*. And therefore, the absent task is not included in the maximum.

        .. seealso::

            - Binary :meth:`Model.max2`.
            - Function :meth:`Model.span` constraints interval variable to start and end at minimum and maximum of the given set of intervals.
        """
        out_params: list[_Argument] = [IntExpr._wrap_list(args)]
        return IntExpr(self, "intMax", out_params)

    def min(self, args: Iterable[IntExpr | int | bool]) -> IntExpr:
        r"""
        Creates an integer expression for the minimum of the arguments.

        :param args: Array of integer expressions to compute minimum of.
        :type args: IntExpr[]

        :returns: The resulting integer expression
        :rtype: IntExpr

        Absent arguments are ignored as if they were not specified in the input array `args`. Minimum of an empty set (i.e. `min([])` is *absent*. The minimum is *absent* also if all arguments are *absent*.

        Note that binary function :meth:`Model.min2` handles absent values differently. For example, when `x` is *absent* then: 

        * `min2(x, 5)` is *absent*.
        * `min([x, 5])` is 5.
        * `min([x])` is *absent*.

        In the following example, we compute the time when the first task of `tasks` starts, i.e. the minimum of the starting times.

        Notice that when a task is *absent* (not executed), its end time is *absent*. And therefore, the absent task is not included in the minimum.

        .. seealso::

            - Binary :meth:`Model.min2`.
            - Function :meth:`Model.span` constraints interval variable to start and end at minimum and maximum of the given set of intervals.
        """
        out_params: list[_Argument] = [IntExpr._wrap_list(args)]
        return IntExpr(self, "intMin", out_params)

    def _int_present_linear_expr(self, coefficients: Iterable[int | bool], expressions: Iterable[IntExpr | int | bool], constantTerm: int | bool = 0) -> IntExpr:
        out_params: list[_Argument] = [_wrap_int_list(coefficients), IntExpr._wrap_list(expressions), _wrap_int(constantTerm)]
        return IntExpr(self, "intPresentLinearExpr", out_params)

    def _int_optional_linear_expr(self, coefficients: Iterable[int | bool], expressions: Iterable[IntExpr | int | bool], constantTerm: int | bool = 0) -> IntExpr:
        out_params: list[_Argument] = [_wrap_int_list(coefficients), IntExpr._wrap_list(expressions), _wrap_int(constantTerm)]
        return IntExpr(self, "intOptionalLinearExpr", out_params)

    def lex_le(self, lhs: Iterable[IntExpr | int | bool], rhs: Iterable[IntExpr | int | bool]) -> Constraint:
        """#doc[Model.lexLe]"""
        out_params: list[_Argument] = [IntExpr._wrap_list(lhs), IntExpr._wrap_list(rhs)]
        return Constraint(self, "intLexLe", out_params)

    def lex_lt(self, lhs: Iterable[IntExpr | int | bool], rhs: Iterable[IntExpr | int | bool]) -> Constraint:
        """#doc[Model.lexLt]"""
        out_params: list[_Argument] = [IntExpr._wrap_list(lhs), IntExpr._wrap_list(rhs)]
        return Constraint(self, "intLexLt", out_params)

    def lex_ge(self, lhs: Iterable[IntExpr | int | bool], rhs: Iterable[IntExpr | int | bool]) -> Constraint:
        """#doc[Model.lexGe]"""
        out_params: list[_Argument] = [IntExpr._wrap_list(lhs), IntExpr._wrap_list(rhs)]
        return Constraint(self, "intLexGe", out_params)

    def lex_gt(self, lhs: Iterable[IntExpr | int | bool], rhs: Iterable[IntExpr | int | bool]) -> Constraint:
        """#doc[Model.lexGt]"""
        out_params: list[_Argument] = [IntExpr._wrap_list(lhs), IntExpr._wrap_list(rhs)]
        return Constraint(self, "intLexGt", out_params)

    def start(self, interval: IntervalVar) -> IntExpr:
        r"""
        Creates an integer expression for the start time of an interval variable.

        :param interval: The interval variable.
        :type interval: IntervalVar

        :returns: The resulting integer expression
        :rtype: IntExpr

        If the interval is absent, the resulting expression is also absent.

        In the following example, we constraint interval variable `y` to start after the end of `y` with a delay of at least 10. In addition, we constrain the length of `x` to be less or equal to the length of `y`.

        When `x` or `y` is *absent* then value of both constraints above is *absent* and therefore they are satisfied.

        .. seealso::

            - :meth:`IntervalVar.start` is equivalent function on :class:`IntervalVar`.
            - Function :meth:`Model.startOfOr` is a similar function that replaces value _absent_ by a constant.
        """
        out_params: list[_Argument] = [IntervalVar._wrap(interval)]
        return IntExpr(self, "startOf", out_params)

    def end(self, interval: IntervalVar) -> IntExpr:
        r"""
        Creates an integer expression for the end time of an interval variable.

        :param interval: The interval variable.
        :type interval: IntervalVar

        :returns: The resulting integer expression
        :rtype: IntExpr

        If the interval is absent, the resulting expression is also absent.

        In the following example, we constraint interval variable `y` to start after the end of `y` with a delay of at least 10. In addition, we constrain the length of `x` to be less or equal to the length of `y`.

        When `x` or `y` is *absent* then value of both constraints above is *absent* and therefore they are satisfied.

        .. seealso::

            - :meth:`IntervalVar.end` is equivalent function on :class:`IntervalVar`.
            - Function :meth:`Model.endOfOr` is a similar function that replaces value _absent_ by a constant.
        """
        out_params: list[_Argument] = [IntervalVar._wrap(interval)]
        return IntExpr(self, "endOf", out_params)

    def length(self, interval: IntervalVar) -> IntExpr:
        r"""
        Creates an integer expression for the duration (end - start) of an interval variable.

        :param interval: The interval variable.
        :type interval: IntervalVar

        :returns: The resulting integer expression
        :rtype: IntExpr

        If the interval is absent, the resulting expression is also absent.

        In the following example, we constraint interval variable `y` to start after the end of `y` with a delay of at least 10. In addition, we constrain the length of `x` to be less or equal to the length of `y`.

        When `x` or `y` is *absent* then value of both constraints above is *absent* and therefore they are satisfied.

        .. seealso::

            - :meth:`IntervalVar.length` is equivalent function on :class:`IntervalVar`.
            - Function :meth:`Model.lengthOfOr` is a similar function that replaces value _absent_ by a constant.
        """
        out_params: list[_Argument] = [IntervalVar._wrap(interval)]
        return IntExpr(self, "lengthOf", out_params)

    def start_or_else(self, interval: IntervalVar, absentValue: int | bool) -> IntExpr:
        r"""
        Creates an integer expression for the start time of the interval variable. If the interval is absent, then its value is `absentValue`.

        :param interval: The interval variable.
        :type interval: IntervalVar
        :param absentValue: The value to use when the interval is absent.
        :type absentValue: int

        :returns: The resulting integer expression
        :rtype: IntExpr

        This function is equivalent to `startOr(interval).guard(absentValue)`.

        .. seealso::

            - :meth:`Model.start_or_else`
            - :meth:`Model.guard`
        """
        out_params: list[_Argument] = [IntervalVar._wrap(interval), _wrap_int(absentValue)]
        return IntExpr(self, "startOr", out_params)

    def end_or_else(self, interval: IntervalVar, absentValue: int | bool) -> IntExpr:
        r"""
        Creates an integer expression for the end time of the interval variable. If the interval is absent, then its value is `absentValue`.

        :param interval: The interval variable.
        :type interval: IntervalVar
        :param absentValue: The value to use when the interval is absent.
        :type absentValue: int

        :returns: The resulting integer expression
        :rtype: IntExpr

        This function is equivalent to `endOr(interval).guard(absentValue)`.

        .. seealso::

            - :meth:`Model.end_or_else`
            - :meth:`Model.guard`
        """
        out_params: list[_Argument] = [IntervalVar._wrap(interval), _wrap_int(absentValue)]
        return IntExpr(self, "endOr", out_params)

    def length_or_else(self, interval: IntervalVar, absentValue: int | bool) -> IntExpr:
        r"""
        Creates an integer expression for the duration (end - start) of the interval variable. If the interval is absent, then its value is `absentValue`.

        :param interval: The interval variable.
        :type interval: IntervalVar
        :param absentValue: The value to use when the interval is absent.
        :type absentValue: int

        :returns: The resulting integer expression
        :rtype: IntExpr

        This function is equivalent to `lengthOr(interval).guard(absentValue)`.

        .. seealso::

            - :meth:`Model.length_or_else`
            - :meth:`Model.guard`
        """
        out_params: list[_Argument] = [IntervalVar._wrap(interval), _wrap_int(absentValue)]
        return IntExpr(self, "lengthOr", out_params)

    def _alternative_cost(self, main: IntervalVar, options: Iterable[IntervalVar], weights: Iterable[int | bool]) -> IntExpr:
        out_params: list[_Argument] = [IntervalVar._wrap(main), IntervalVar._wrap_list(options), _wrap_int_list(weights)]
        return IntExpr(self, "intAlternativeCost", out_params)

    def end_before_end(self, predecessor: IntervalVar, successor: IntervalVar, delay: IntExpr | int | bool = 0) -> Constraint:
        r"""
        Creates a precedence constraint between two interval variables.

        :param predecessor: The predecessor interval variable.
        :type predecessor: IntervalVar
        :param successor: The successor interval variable.
        :type successor: IntervalVar
        :param delay: The minimum delay between intervals.
        :type delay: IntExpr

        :returns: The precedence constraint.
        :rtype: Constraint

        Same as:

        In other words, end of `predecessor` plus `delay` must be less than or equal to end of `successor`.

        When one of the two interval variables is absent, then the constraint is satisfied.

        .. seealso::

            - :meth:`IntervalVar.end_before_end` is equivalent function on :class:`IntervalVar`.
            - :meth:`Model.constraint`
            - :meth:`IntervalVar.start`, :meth:`IntervalVar.end`
            - :meth:`IntExpr.le`
        """
        out_params: list[_Argument] = [IntervalVar._wrap(predecessor), IntervalVar._wrap(successor), IntExpr._wrap(delay)]
        return Constraint(self, "endBeforeEnd", out_params)

    def end_before_start(self, predecessor: IntervalVar, successor: IntervalVar, delay: IntExpr | int | bool = 0) -> Constraint:
        r"""
        Creates a precedence constraint between two interval variables.

        :param predecessor: The predecessor interval variable.
        :type predecessor: IntervalVar
        :param successor: The successor interval variable.
        :type successor: IntervalVar
        :param delay: The minimum delay between intervals.
        :type delay: IntExpr

        :returns: The precedence constraint.
        :rtype: Constraint

        Same as:

        In other words, end of `predecessor` plus `delay` must be less than or equal to start of `successor`.

        When one of the two interval variables is absent, then the constraint is satisfied.

        .. seealso::

            - :meth:`IntervalVar.end_before_start` is equivalent function on :class:`IntervalVar`.
            - :meth:`Model.constraint`
            - :meth:`IntervalVar.start`, :meth:`IntervalVar.end`
            - :meth:`IntExpr.le`
        """
        out_params: list[_Argument] = [IntervalVar._wrap(predecessor), IntervalVar._wrap(successor), IntExpr._wrap(delay)]
        return Constraint(self, "endBeforeStart", out_params)

    def start_before_end(self, predecessor: IntervalVar, successor: IntervalVar, delay: IntExpr | int | bool = 0) -> Constraint:
        r"""
        Creates a precedence constraint between two interval variables.

        :param predecessor: The predecessor interval variable.
        :type predecessor: IntervalVar
        :param successor: The successor interval variable.
        :type successor: IntervalVar
        :param delay: The minimum delay between intervals.
        :type delay: IntExpr

        :returns: The precedence constraint.
        :rtype: Constraint

        Same as:

        In other words, start of `predecessor` plus `delay` must be less than or equal to end of `successor`.

        When one of the two interval variables is absent, then the constraint is satisfied.

        .. seealso::

            - :meth:`IntervalVar.start_before_end` is equivalent function on :class:`IntervalVar`.
            - :meth:`Model.constraint`
            - :meth:`IntervalVar.start`, :meth:`IntervalVar.end`
            - :meth:`IntExpr.le`
        """
        out_params: list[_Argument] = [IntervalVar._wrap(predecessor), IntervalVar._wrap(successor), IntExpr._wrap(delay)]
        return Constraint(self, "startBeforeEnd", out_params)

    def start_before_start(self, predecessor: IntervalVar, successor: IntervalVar, delay: IntExpr | int | bool = 0) -> Constraint:
        r"""
        Creates a precedence constraint between two interval variables.

        :param predecessor: The predecessor interval variable.
        :type predecessor: IntervalVar
        :param successor: The successor interval variable.
        :type successor: IntervalVar
        :param delay: The minimum delay between intervals.
        :type delay: IntExpr

        :returns: The precedence constraint.
        :rtype: Constraint

        Same as:

        In other words, start of `predecessor` plus `delay` must be less than or equal to start of `successor`.

        When one of the two interval variables is absent, then the constraint is satisfied.

        .. seealso::

            - :meth:`IntervalVar.start_before_start` is equivalent function on :class:`IntervalVar`.
            - :meth:`Model.constraint`
            - :meth:`IntervalVar.start`, :meth:`IntervalVar.end`
            - :meth:`IntExpr.le`
        """
        out_params: list[_Argument] = [IntervalVar._wrap(predecessor), IntervalVar._wrap(successor), IntExpr._wrap(delay)]
        return Constraint(self, "startBeforeStart", out_params)

    def end_at_end(self, predecessor: IntervalVar, successor: IntervalVar, delay: IntExpr | int | bool = 0) -> Constraint:
        r"""
        Creates a precedence constraint between two interval variables.

        :param predecessor: The predecessor interval variable.
        :type predecessor: IntervalVar
        :param successor: The successor interval variable.
        :type successor: IntervalVar
        :param delay: The minimum delay between intervals.
        :type delay: IntExpr

        :returns: The precedence constraint.
        :rtype: Constraint

        Same as:

        In other words, end of `predecessor` plus `delay` must be equal to end of `successor`.

        When one of the two interval variables is absent, then the constraint is satisfied.

        .. seealso::

            - :meth:`IntervalVar.end_at_end` is equivalent function on :class:`IntervalVar`.
            - :meth:`Model.constraint`
            - :meth:`IntervalVar.start`, :meth:`IntervalVar.end`
            - :meth:`IntExpr.eq`
        """
        out_params: list[_Argument] = [IntervalVar._wrap(predecessor), IntervalVar._wrap(successor), IntExpr._wrap(delay)]
        return Constraint(self, "endAtEnd", out_params)

    def end_at_start(self, predecessor: IntervalVar, successor: IntervalVar, delay: IntExpr | int | bool = 0) -> Constraint:
        r"""
        Creates a precedence constraint between two interval variables.

        :param predecessor: The predecessor interval variable.
        :type predecessor: IntervalVar
        :param successor: The successor interval variable.
        :type successor: IntervalVar
        :param delay: The minimum delay between intervals.
        :type delay: IntExpr

        :returns: The precedence constraint.
        :rtype: Constraint

        Same as:

        In other words, end of `predecessor` plus `delay` must be equal to start of `successor`.

        When one of the two interval variables is absent, then the constraint is satisfied.

        .. seealso::

            - :meth:`IntervalVar.end_at_start` is equivalent function on :class:`IntervalVar`.
            - :meth:`Model.constraint`
            - :meth:`IntervalVar.start`, :meth:`IntervalVar.end`
            - :meth:`IntExpr.eq`
        """
        out_params: list[_Argument] = [IntervalVar._wrap(predecessor), IntervalVar._wrap(successor), IntExpr._wrap(delay)]
        return Constraint(self, "endAtStart", out_params)

    def start_at_end(self, predecessor: IntervalVar, successor: IntervalVar, delay: IntExpr | int | bool = 0) -> Constraint:
        r"""
        Creates a precedence constraint between two interval variables.

        :param predecessor: The predecessor interval variable.
        :type predecessor: IntervalVar
        :param successor: The successor interval variable.
        :type successor: IntervalVar
        :param delay: The minimum delay between intervals.
        :type delay: IntExpr

        :returns: The precedence constraint.
        :rtype: Constraint

        Same as:

        In other words, start of `predecessor` plus `delay` must be equal to end of `successor`.

        When one of the two interval variables is absent, then the constraint is satisfied.

        .. seealso::

            - :meth:`IntervalVar.start_at_end` is equivalent function on :class:`IntervalVar`.
            - :meth:`Model.constraint`
            - :meth:`IntervalVar.start`, :meth:`IntervalVar.end`
            - :meth:`IntExpr.eq`
        """
        out_params: list[_Argument] = [IntervalVar._wrap(predecessor), IntervalVar._wrap(successor), IntExpr._wrap(delay)]
        return Constraint(self, "startAtEnd", out_params)

    def start_at_start(self, predecessor: IntervalVar, successor: IntervalVar, delay: IntExpr | int | bool = 0) -> Constraint:
        r"""
        Creates a precedence constraint between two interval variables.

        :param predecessor: The predecessor interval variable.
        :type predecessor: IntervalVar
        :param successor: The successor interval variable.
        :type successor: IntervalVar
        :param delay: The minimum delay between intervals.
        :type delay: IntExpr

        :returns: The precedence constraint.
        :rtype: Constraint

        Same as:

        In other words, start of `predecessor` plus `delay` must be equal to start of `successor`.

        When one of the two interval variables is absent, then the constraint is satisfied.

        .. seealso::

            - :meth:`IntervalVar.start_at_start` is equivalent function on :class:`IntervalVar`.
            - :meth:`Model.constraint`
            - :meth:`IntervalVar.start`, :meth:`IntervalVar.end`
            - :meth:`IntExpr.eq`
        """
        out_params: list[_Argument] = [IntervalVar._wrap(predecessor), IntervalVar._wrap(successor), IntExpr._wrap(delay)]
        return Constraint(self, "startAtStart", out_params)

    def alternative(self, main: IntervalVar, options: Iterable[IntervalVar]) -> Constraint:
        r"""
        Alternative constraint models a choice between different ways to execute an interval.

        :param main: The main interval variable.
        :type main: IntervalVar
        :param options: Array of optional interval variables to choose from.
        :type options: IntervalVar[]

        :returns: The alternative constraint.
        :rtype: Constraint

        Alternative constraint is a way to model various kinds of choices. For example, we can model a task that could be done by worker A, B, or C. To model such alternative, we use interval variable `main` that represents the task regardless the chosen worker and three interval variables `options = [A, B, C]` that represent the task when done by worker A, B, or C. Interval variables `A`, `B`, and `C` should be optional. This way, if e.g. option B is chosen, then `B` will be *present* and equal to `main` (they will start at the same time and end at the same time), the remaining options, A and C, will be *absent*.

        We may also decide not to execute the `main` task at all (if it is optional). Then `main` will be *absent* and all options `A`, `B` and `C` will be *absent* too.

        #### Formal definition

        The constraint `alternative(main, options)` is satisfied in the following two cases:
        1. Interval `main` is *absent* and all `options[i]` are *absent* too.
        2. Interval `main` is *present* and exactly one of `options[i]` is *present* (the remaining options are *absent*).    Let `k` be the index of the present option.    Then `main.start() == options[k].start()` and `main.end() == options[k].end()`.

        Let's consider task T, which can be done by workers A, B, or C. The length of the task and a cost associated with it depends on the chosen worker: 

        * If done by worker A, then its length is 10, and the cost is 5.
        * If done by worker B, then its length is 20, and the cost is 2.
        * If done by worker C, then its length is 3, and the cost is 10.

        Each worker can execute only one task at a time. However, the remaining tasks are omitted in the model below. The objective could be, e.g., to minimize the total cost (also omitted in the model).
        """
        out_params: list[_Argument] = [IntervalVar._wrap(main), IntervalVar._wrap_list(options)]
        return Constraint(self, "alternative", out_params)

    def interval_var_element(self, slots: Iterable[IntervalVar], index: IntExpr | int | bool, value: IntervalVar) -> Constraint:
        """#doc[Model.intervalVarElement]"""
        out_params: list[_Argument] = [IntervalVar._wrap_list(slots), IntExpr._wrap(index), IntervalVar._wrap(value)]
        return Constraint(self, "intervalVarElement", out_params)

    def increasing_interval_var_element(self, slots: Iterable[IntervalVar], index: IntExpr | int | bool, value: IntervalVar) -> Constraint:
        """#doc[Model.increasingIntervalVarElement]"""
        out_params: list[_Argument] = [IntervalVar._wrap_list(slots), IntExpr._wrap(index), IntervalVar._wrap(value)]
        return Constraint(self, "increasingIntervalVarElement", out_params)

    def itv_mapping(self, tasks: Iterable[IntervalVar], slots: Iterable[IntervalVar], indices: Iterable[IntExpr | int | bool]) -> Constraint:
        r"""
        Maps tasks to slots according to indices, synchronizing each task with its assigned slot.

        :param tasks: Array of interval variables to map.
        :type tasks: IntervalVar[]
        :param slots: Array of interval variables to map to.
        :type slots: IntervalVar[]
        :param indices: Array of integer expressions that specify the mapping.
        :type indices: IntExpr[]

        :returns: The interval mapping constraint.
        :rtype: Constraint

        Each task is synchronized with the slot it is assigned to. Multiple tasks can be
        assigned to the same slot. A slot without any task is *absent*. Absent tasks are
        not assigned to any slot (their index value is *absent*).  Slots are sorted by
        both start and end. Absent slots are at the end of the array.

        The constraint can be used to form batches of synchronized tasks (so-called
        *p-batching*). In this case `slots` corresponds to batches. The size of the
        batches can be limited using, e.g., :meth:`Model.pack` constraint.

        #### Formal definition

        Let :math:`T` be the number of tasks (the length of the
        array `tasks`). The number of the indices must also be :math:`T` (arrays `tasks` and
        `indices` must have the same length).  Let `tasks[t]` be one of the tasks, i.e.,
        :math:`\mathtt{t} \in \{0,1,\dots T-1\}`. Then `indices[t]` is the index of the slot
        the task `tasks[t]` is assigned to.  Only present tasks are assigned:

        .. math::

            \mathtt{
              \forall t \in \mathrm{ \{0,\dots,T-1\} }: \quad presenceOf(tasks[t]) \,\Leftrightarrow\, presenceOf(indices[t])
            }

        Each task is synchronized with the slot to which it is assigned:

        .. math::

            \begin{aligned}
            \mathtt{\forall t \in \mathrm{ \{0,\dots,T-1\} } \text{ such that } tasks[t] \ne \text{absent:}} \\
                \mathtt{slots[indices[t]]} &\ne \textrm{absent} \\
                \mathtt{startOf(tasks[t])} &= \mathtt{startOf(slots[indices[t]]) }\\
                \mathtt{endOf(tasks[t])} &= \mathtt{endOf(slots[indices[t]])}
            \end{aligned}

        A slot is present if and only if there is a task assigned to it:

        .. math::

            \forall \mathtt{s} \in \{0,\dots,S-1\}:\;
            \mathtt{presenceOf(tasks[s])} \;\Leftrightarrow\; (\exists \mathtt{t} \in 0,\dots,T-1: \mathtt{indices[t]=s})

        Absent slots are positioned at the end of the array:

        .. math::

            \mathtt{
               \forall s \in \mathrm{ \{1,\dots,S-1\} }:\, presenceOf(slots[s]) \Rightarrow presenceOf(slots[s-1])
            }

        Present slots are sorted by both start and end:

        .. math::

            \begin{aligned}
            \mathtt{\forall s \in \mathrm{1,\dots,S-1} \text{ such that } slots[s] \ne \text{absent:}} \\
                \mathtt{startOf(slots[s-1])} &\le \mathtt{startOf(slots[s]) }
                \\
                \mathtt{endOf(slots[s-1])} &\le \mathtt{endOf(slots[s])}
            \end{aligned}

        The amount of the propagation for this constraint can be controlled by parameter
        :meth:`Parameters.itvMappingPropagationLevel`.

        .. seealso::

            - :meth:`Model.pack` for limiting the amount of tasks assigned to a slot.
        """
        out_params: list[_Argument] = [IntervalVar._wrap_list(tasks), IntervalVar._wrap_list(slots), IntExpr._wrap_list(indices)]
        return Constraint(self, "itvMapping", out_params)

    def span(self, main: IntervalVar, covered: Iterable[IntervalVar]) -> Constraint:
        r"""
        Constraints an interval variable to span (cover) a set of other interval variables.

        :param main: The spanning interval variable.
        :type main: IntervalVar
        :param covered: The set of interval variables to cover.
        :type covered: IntervalVar[]

        :returns: The span constraint.
        :rtype: Constraint

        Span constraint can be used to model, for example, a composite task that consists of several subtasks.

        The constraint makes sure that interval variable `main` starts with the first interval in `covered` and ends with the last interval in `covered`. Absent interval variables in `covered` are ignored.

        #### Formal definition

        Span constraint is satisfied in one of the following two cases:

        * Interval variable `main` is absent and all interval variables in `covered` are absent too.
        * Interval variable `main` is present, at least one interval in `covered` is present and:

           * `main.start()` is equal to the minimum starting time of all present intervals in `covered`.
           * `main.end()` is equal to the maximum ending time of all present intervals in `covered`.

        Let's consider composite task `T`, which consists of 3 subtasks: `T1`, `T2`, and `T3`. Subtasks are independent, could be processed in any order, and may overlap. However, task T is blocking a particular location, and no other task can be processed there. The location is blocked as soon as the first task from `T1`, `T2`, `T3` starts, and it remains blocked until the last one of them finishes.

        .. seealso::

            - :meth:`IntervalVar.span` is equivalent function on :class:`IntervalVar`.
        """
        out_params: list[_Argument] = [IntervalVar._wrap(main), IntervalVar._wrap_list(covered)]
        return Constraint(self, "span", out_params)

    def position(self, interval: IntervalVar, sequence: SequenceVar) -> IntExpr:
        r"""
        Creates an expression equal to the position of the `interval` on the `sequence`.

        :param interval: The interval variable.
        :type interval: IntervalVar
        :param sequence: The sequence variable.
        :type sequence: SequenceVar

        :returns: The resulting integer expression
        :rtype: IntExpr

        In the solution, the interval which is scheduled first has position 0, the second interval has position 1, etc. The position of an absent interval is `absent`.

        The `position` expression cannot be used with interval variables of possibly zero length (because the position of two simultaneous zero-length intervals would be undefined). Also, `position` cannot be used in case of :meth:`Model.no_overlap` constraint with transition times.

        .. seealso::

            - :meth:`IntervalVar.position` is equivalent function on :class:`IntervalVar`.
            - :meth:`Model.no_overlap` for constraints on overlapping intervals.
            - :meth:`Model.sequence_var` for creating sequence variables.
        """
        out_params: list[_Argument] = [IntervalVar._wrap(interval), SequenceVar._wrap(sequence)]
        return IntExpr(self, "position", out_params)

    def _same_sequence(self, sequence1: SequenceVar, sequence2: SequenceVar) -> Constraint:
        out_params: list[_Argument] = [SequenceVar._wrap(sequence1), SequenceVar._wrap(sequence2)]
        return Constraint(self, "sameSequence", out_params)

    def _same_sequence_group(self, sequences: Iterable[SequenceVar]) -> Constraint:
        out_params: list[_Argument] = [SequenceVar._wrap_list(sequences)]
        return Constraint(self, "sameSequenceGroup", out_params)

    def pulse(self, interval: IntervalVar, height: IntExpr | int | bool) -> CumulExpr:
        r"""
        Creates cumulative function (expression) _pulse_ for the given interval variable and height.

        :param interval: The interval variable.
        :type interval: IntervalVar
        :param height: The height value.
        :type height: IntExpr

        :returns: The resulting cumulative expression
        :rtype: CumulExpr

        Pulse can be used to model a resource requirement during an interval variable. The given amount `height` of the resource is used throughout the interval (from start to end).

        #### Formal definition

        Pulse creates a cumulative function which has the value:

        * `0` before `interval.start()`,
        * `height` between `interval.start()` and `interval.end()`,
        * `0` after `interval.end()`

        If `interval` is absent, the pulse is `0` everywhere.

        The `height` can be a constant value or an expression. In particular, the `height` can be given by an :class:`IntVar`. In such a case, the `height` is unknown at the time of the model creation but is determined during the search.

        Note that the `interval` and the `height` may have different presence statuses (when the `height` is given by a variable or an expression). In this case, the pulse is present only if both the `interval` and the `height` are present. Therefore, it is helpful to constrain the `height` to have the same presence status as the `interval`.

        Cumulative functions can be combined using :meth:`Model.cumul_plus`, :meth:`Model.cumul_minus`, :meth:`Model.cumul_neg` and :meth:`Model.cumul_sum`. A cumulative function's minimum and maximum height can be constrained using :meth:`Model.cumul_le` and :meth:`Model.cumul_ge`.

        Let us consider a set of tasks and a group of 3 workers. Each task requires a certain number of workers (`nbWorkersNeeded`). Our goal is to schedule the tasks so that the length of the schedule (makespan) is minimal.

        In the following example, we create three interval variables `x`, `y`, and `z` that represent some tasks. Variables `x` and `y` are present, but variable `z` is optional. Each task requires a certain number of workers. The length of the task depends on the assigned number of workers. The number of assigned workers is modeled using integer variables `workersX`, `workersY`, and `workersZ`.

        There are 7 workers. Therefore, at any time, the sum of the workers assigned to the running tasks must be less or equal to 7.

        If the task `z` is absent, then the variable `workersZ` has no meaning, and therefore, it should also be absent.

        .. seealso::

            - :meth:`IntervalVar.pulse` is equivalent function on :class:`IntervalVar`.
            - :meth:`Model.step_at_start`, :meth:`Model.step_at_end`, :meth:`Model.step_at` for other basic cumulative functions.
            - :meth:`Model.cumul_le` and :meth:`Model.cumul_ge` for constraints on cumulative functions.
        """
        out_params: list[_Argument] = [IntervalVar._wrap(interval), IntExpr._wrap(height)]
        return CumulExpr(self, "pulse", out_params)

    def step_at_start(self, interval: IntervalVar, height: IntExpr | int | bool) -> CumulExpr:
        r"""
        Creates cumulative function (expression) that changes value at start of the interval variable by the given height.

        :param interval: The interval variable.
        :type interval: IntervalVar
        :param height: The height value.
        :type height: IntExpr

        :returns: The resulting cumulative expression
        :rtype: CumulExpr

        Cumulative *step* functions could be used to model a resource that is consumed or produced and, therefore, changes in amount over time. Examples of such a resource are a battery, an account balance, a product's stock, etc.

        A `step_at_start` can change the amount of such resource at the start of a given variable. The amount is changed by the given `height`, which can be positive or negative.

        The `height` can be a constant value or an expression. In particular, the `height` can be given by an :class:`IntVar`. In such a case, the `height` is unknown at the time of the model creation but is determined during the search.

        Note that the `interval` and the `height` may have different presence statuses (when the `height` is given by a variable or an expression). In this case, the step is present only if both the `interval` and the `height` are present. Therefore, it is helpful to constrain the `height` to have the same presence status as the `interval`.

        Cumulative steps could be combined using :meth:`Model.cumul_plus`,:meth:`Model.cumul_minus`, :meth:`Model.cumul_neg` and :meth:`Model.cumul_sum`. A cumulative function's minimum and maximum height can be constrained using :meth:`Model.cumul_le` and :meth:`Model.cumul_ge`.

        #### Formal definition

        stepAtStart creates a cumulative function which has the value:

        * `0` before `interval.start()`,
        * `height` after `interval.start()`.

        If the `interval` or the `height` is *absent*, the created cumulative function is `0` everywhere.

        Let us consider a set of tasks. Each task either costs a certain amount of money or makes some money. Money is consumed at the start of a task and produced at the end. We have an initial amount of money `initialMoney`, and we want to schedule the tasks so that we do not run out of money (i.e., the amount is always non-negative).

        Tasks cannot overlap. Our goal is to find the shortest schedule possible.

        .. seealso::

            - :meth:`IntervalVar.step_at_start` is equivalent function on :class:`IntervalVar`.
            - :meth:`Model.step_at_end`, :meth:`Model.step_at`, :meth:`Model.pulse` for other basic cumulative functions.
            - :meth:`Model.cumul_le` and :meth:`Model.cumul_ge` for constraints on cumulative functions.
        """
        out_params: list[_Argument] = [IntervalVar._wrap(interval), IntExpr._wrap(height)]
        return CumulExpr(self, "stepAtStart", out_params)

    def step_at_end(self, interval: IntervalVar, height: IntExpr | int | bool) -> CumulExpr:
        r"""
        Creates cumulative function (expression) that changes value at end of the interval variable by the given height.

        :param interval: The interval variable.
        :type interval: IntervalVar
        :param height: The height value.
        :type height: IntExpr

        :returns: The resulting cumulative expression
        :rtype: CumulExpr

        Cumulative *step* functions could be used to model a resource that is consumed or produced and, therefore, changes in amount over time. Examples of such a resource are a battery, an account balance, a product's stock, etc.

        A `step_at_end` can change the amount of such resource at the end of a given variable. The amount is changed by the given `height`, which can be positive or negative.

        The `height` can be a constant value or an expression. In particular, the `height` can be given by an :class:`IntVar`. In such a case, the `height` is unknown at the time of the model creation but is determined during the search.

        Note that the `interval` and the `height` may have different presence statuses (when the `height` is given by a variable or an expression). In this case, the step is present only if both the `interval` and the `height` are present. Therefore, it is helpful to constrain the `height` to have the same presence status as the `interval`.

        Cumulative steps could be combined using :meth:`Model.cumul_plus`,:meth:`Model.cumul_minus`, :meth:`Model.cumul_neg` and :meth:`Model.cumul_sum`. A cumulative function's minimum and maximum height can be constrained using :meth:`Model.cumul_le` and :meth:`Model.cumul_ge`.

        #### Formal definition

        stepAtEnd creates a cumulative function which has the value:

        * `0` before `interval.end()`,
        * `height` after `interval.end()`.

        If the `interval` or the `height` is *absent*, the created cumulative function is `0` everywhere.

        Let us consider a set of tasks. Each task either costs a certain amount of money or makes some money. Money is consumed at the start of a task and produced at the end. We have an initial amount of money `initialMoney`, and we want to schedule the tasks so that we do not run out of money (i.e., the amount is always non-negative).

        Tasks cannot overlap. Our goal is to find the shortest schedule possible.

        .. seealso::

            - :meth:`IntervalVar.step_at_end` is equivalent function on :class:`IntervalVar`.
            - :meth:`Model.step_at_start`, :meth:`Model.step_at`, :meth:`Model.pulse` for other basic cumulative functions.
            - :meth:`Model.cumul_le` and :meth:`Model.cumul_ge` for constraints on cumulative functions.
        """
        out_params: list[_Argument] = [IntervalVar._wrap(interval), IntExpr._wrap(height)]
        return CumulExpr(self, "stepAtEnd", out_params)

    def step_at(self, x: int | bool, height: IntExpr | int | bool) -> CumulExpr:
        r"""
        Creates cumulative function (expression) that changes value at `x` by the given `height`. The height can be positive or negative, and it can be given by a constant or an expression (for example, by {@meth Model.intVar}).

        :param x: The point at which the cumulative function changes value.
        :type x: int
        :param height: The height value.
        :type height: IntExpr

        :returns: The resulting cumulative expression
        :rtype: CumulExpr

        Function stepAt is functionally the same as :meth:`Model.step_at_start` and :meth:`Model.step_at_end`. However, the time of the change is given by the constant value `x` instead of by the start/end of an interval variable.

        #### Formal definition

        `step_at` creates a cumulative function which has the value:

        * 0 before `x`,
        * `height` after `x`.

        .. seealso::

            - :meth:`Model.step_at_start`, :meth:`Model.step_at_end` for an example with `stepAt`.
            - :meth:`Model.cumul_le` and :meth:`Model.cumul_ge` for constraints on cumulative functions.
        """
        out_params: list[_Argument] = [_wrap_int(x), IntExpr._wrap(height)]
        return CumulExpr(self, "stepAt", out_params)

    def cumul_sum(self, array: Iterable[CumulExpr]) -> CumulExpr:
        r"""
        Sum of cumulative expressions.

        :param array: Array of cumulative expressions to sum.
        :type array: cumulExprArray

        :returns: The resulting cumulative expression
        :rtype: CumulExpr

        Computes the sum of cumulative functions. The sum can be used, e.g., to combine contributions of individual tasks to total resource consumption.

        .. seealso::

            - :meth:`Model.cumul_plus`, :meth:`Model.cumul_minus`, :meth:`Model.cumul_neg` for other ways to combine cumulative functions.
        """
        out_params: list[_Argument] = [CumulExpr._wrap_list(array)]
        return CumulExpr(self, "cumulSum", out_params)

    def _cumul_max_profile(self, cumul: CumulExpr, profile: IntStepFunction) -> Constraint:
        out_params: list[_Argument] = [CumulExpr._wrap(cumul), IntStepFunction._wrap(profile)]
        return Constraint(self, "cumulMaxProfile", out_params)

    def _cumul_min_profile(self, cumul: CumulExpr, profile: IntStepFunction) -> Constraint:
        out_params: list[_Argument] = [CumulExpr._wrap(cumul), IntStepFunction._wrap(profile)]
        return Constraint(self, "cumulMinProfile", out_params)

    def _cumul_stairs(self, atoms: Iterable[CumulExpr]) -> CumulExpr:
        out_params: list[_Argument] = [CumulExpr._wrap_list(atoms)]
        return CumulExpr(self, "cumulStairs", out_params)

    def _precedence_energy_before(self, main: IntervalVar, others: Iterable[IntervalVar], heights: Iterable[int | bool], capacity: int | bool) -> Constraint:
        out_params: list[_Argument] = [IntervalVar._wrap(main), IntervalVar._wrap_list(others), _wrap_int_list(heights), _wrap_int(capacity)]
        return Constraint(self, "precedenceEnergyBefore", out_params)

    def _precedence_energy_after(self, main: IntervalVar, others: Iterable[IntervalVar], heights: Iterable[int | bool], capacity: int | bool) -> Constraint:
        out_params: list[_Argument] = [IntervalVar._wrap(main), IntervalVar._wrap_list(others), _wrap_int_list(heights), _wrap_int(capacity)]
        return Constraint(self, "precedenceEnergyAfter", out_params)

    def step_function_sum(self, func: IntStepFunction, interval: IntervalVar) -> IntExpr:
        r"""
        Computes sum of values of the step function `func` over the interval `interval`.

        :param func: The step function.
        :type func: IntStepFunction
        :param interval: The interval variable.
        :type interval: IntervalVar

        :returns: The resulting integer expression
        :rtype: IntExpr

        The sum is computed over all points in range `interval.start()` .. `interval.end()-1`. The sum includes the function value at the start time but not the value at the end time. If the interval variable has zero length, then the result is 0. If the interval variable is absent, then the result is `absent`.

        **Requirement**: The step function `func` must be non-negative.

        .. seealso::

            - :meth:`IntStepFunction.stepFunctionSum` for the equivalent function on :class:`IntStepFunction`.
        """
        out_params: list[_Argument] = [IntStepFunction._wrap(func), IntervalVar._wrap(interval)]
        return IntExpr(self, "intStepFunctionSum", out_params)

    def _step_function_sum_in_range(self, func: IntStepFunction, interval: IntervalVar, lb: int | bool, ub: int | bool) -> Constraint:
        out_params: list[_Argument] = [IntStepFunction._wrap(func), IntervalVar._wrap(interval), _wrap_int(lb), _wrap_int(ub)]
        return Constraint(self, "intStepFunctionSumInRange", out_params)

    def step_function_eval(self, func: IntStepFunction, arg: IntExpr | int | bool) -> IntExpr:
        r"""
        Evaluates a step function at a given point.

        :param func: The step function.
        :type func: IntStepFunction
        :param arg: The point at which to evaluate the step function.
        :type arg: IntExpr

        :returns: The resulting integer expression
        :rtype: IntExpr

        The result is the value of the step function `func` at the point `arg`. If the value of `arg` is `absent`, then the result is also `absent`.

        By constraining the returned value, it is possible to limit `arg` to be only within certain segments of the segmented function. In particular, functions :meth:`Model.forbid_start` and :meth:`Model.forbid_end` work that way.

        .. seealso::

            - :meth:`IntStepFunction.stepFunctionEval` for the equivalent function on :class:`IntStepFunction`.
            - :meth:`Model.forbid_start`, :meth:`Model.forbid_end` are convenience functions built on top of `stepFunctionEval`.
        """
        out_params: list[_Argument] = [IntStepFunction._wrap(func), IntExpr._wrap(arg)]
        return IntExpr(self, "intStepFunctionEval", out_params)

    def _step_function_eval_in_range(self, func: IntStepFunction, arg: IntExpr | int | bool, lb: int | bool, ub: int | bool) -> Constraint:
        out_params: list[_Argument] = [IntStepFunction._wrap(func), IntExpr._wrap(arg), _wrap_int(lb), _wrap_int(ub)]
        return Constraint(self, "intStepFunctionEvalInRange", out_params)

    def _step_function_eval_not_in_range(self, func: IntStepFunction, arg: IntExpr | int | bool, lb: int | bool, ub: int | bool) -> Constraint:
        out_params: list[_Argument] = [IntStepFunction._wrap(func), IntExpr._wrap(arg), _wrap_int(lb), _wrap_int(ub)]
        return Constraint(self, "intStepFunctionEvalNotInRange", out_params)

    def forbid_extent(self, interval: IntervalVar, func: IntStepFunction) -> Constraint:
        r"""
        Forbid the interval variable to overlap with segments of the function where the value is zero.

        :param interval: The interval variable.
        :type interval: IntervalVar
        :param func: The step function.
        :type func: IntStepFunction

        :returns: The constraint forbidding the extent (entire interval).
        :rtype: Constraint

        This function prevents the specified interval variable from overlapping with segments of the step function where the value is zero. That is, if :math:`[s, e)` is a segment of the step function where the value is zero, then the interval variable either ends before :math:`s` (:math:`\mathtt{interval.end()} \le s`) or starts after :math:`e` (:math:`e \le \mathtt{interval.start()}`).

        .. seealso::

            - :meth:`IntervalVar.forbid_extent` for the equivalent function on :class:`IntervalVar`.
            - :meth:`Model.forbid_start`, :meth:`Model.forbid_end` for similar functions that constrain the start/end of an interval variable.
            - :meth:`Model.step_function_eval` for evaluation of a step function.
        """
        out_params: list[_Argument] = [IntervalVar._wrap(interval), IntStepFunction._wrap(func)]
        return Constraint(self, "forbidExtent", out_params)

    def forbid_start(self, interval: IntervalVar, func: IntStepFunction) -> Constraint:
        r"""
        Constrains the start of the interval variable to be outside of the zero-height segments of the step function.

        :param interval: The interval variable.
        :type interval: IntervalVar
        :param func: The step function.
        :type func: IntStepFunction

        :returns: The constraint forbidding the start point.
        :rtype: Constraint

        This function is equivalent to:

        I.e., the function value at the start of the interval variable cannot be zero.

        .. seealso::

            - :meth:`IntervalVar.forbid_start` for the equivalent function on :class:`IntervalVar`.
            - :meth:`Model.forbid_end` for similar function that constrains end an interval variable.
            - :meth:`Model.step_function_eval` for evaluation of a step function.
        """
        out_params: list[_Argument] = [IntervalVar._wrap(interval), IntStepFunction._wrap(func)]
        return Constraint(self, "forbidStart", out_params)

    def forbid_end(self, interval: IntervalVar, func: IntStepFunction) -> Constraint:
        r"""
        Constrains the end of the interval variable to be outside of the zero-height segments of the step function.

        :param interval: The interval variable.
        :type interval: IntervalVar
        :param func: The step function.
        :type func: IntStepFunction

        :returns: The constraint forbidding the end point.
        :rtype: Constraint

        This function is equivalent to:

        I.e., the function value at the end of the interval variable cannot be zero.

        .. seealso::

            - :meth:`IntervalVar.forbid_end` for the equivalent function on :class:`IntervalVar`.
            - :meth:`Model.forbid_start` for similar function that constrains start an interval variable.
            - :meth:`Model.step_function_eval` for evaluation of a step function.
        """
        out_params: list[_Argument] = [IntervalVar._wrap(interval), IntStepFunction._wrap(func)]
        return Constraint(self, "forbidEnd", out_params)

    def _disjunctive_is_before(self, x: IntervalVar, y: IntervalVar) -> BoolExpr:
        out_params: list[_Argument] = [IntervalVar._wrap(x), IntervalVar._wrap(y)]
        return BoolExpr(self, "disjunctiveIsBefore", out_params)

    def _itv_presence_chain(self, intervals: Iterable[IntervalVar]) -> Constraint:
        out_params: list[_Argument] = [IntervalVar._wrap_list(intervals)]
        return Constraint(self, "itvPresenceChain", out_params)

    def _itv_presence_chain_with_count(self, intervals: Iterable[IntervalVar], count: IntExpr | int | bool) -> Constraint:
        out_params: list[_Argument] = [IntervalVar._wrap_list(intervals), IntExpr._wrap(count)]
        return Constraint(self, "itvPresenceChainWithCount", out_params)

    def _end_before_start_chain(self, intervals: Iterable[IntervalVar]) -> Constraint:
        out_params: list[_Argument] = [IntervalVar._wrap_list(intervals)]
        return Constraint(self, "endBeforeStartChain", out_params)

    def _start_before_start_chain(self, intervals: Iterable[IntervalVar]) -> Constraint:
        out_params: list[_Argument] = [IntervalVar._wrap_list(intervals)]
        return Constraint(self, "startBeforeStartChain", out_params)

    def _end_before_end_chain(self, intervals: Iterable[IntervalVar]) -> Constraint:
        out_params: list[_Argument] = [IntervalVar._wrap_list(intervals)]
        return Constraint(self, "endBeforeEndChain", out_params)

    def _decision_present_int_var(self, variable: IntExpr | int | bool, isLeft: bool) -> _SearchDecision:
        out_params: list[_Argument] = [IntExpr._wrap(variable), _wrap_bool(isLeft)]
        return _SearchDecision(self, "decisionPresentIntVar", out_params)

    def _decision_absent_int_var(self, variable: IntExpr | int | bool, isLeft: bool) -> _SearchDecision:
        out_params: list[_Argument] = [IntExpr._wrap(variable), _wrap_bool(isLeft)]
        return _SearchDecision(self, "decisionAbsentIntVar", out_params)

    def _decision_present_interval_var(self, variable: IntervalVar, isLeft: bool) -> _SearchDecision:
        out_params: list[_Argument] = [IntervalVar._wrap(variable), _wrap_bool(isLeft)]
        return _SearchDecision(self, "decisionPresentIntervalVar", out_params)

    def _decision_absent_interval_var(self, variable: IntervalVar, isLeft: bool) -> _SearchDecision:
        out_params: list[_Argument] = [IntervalVar._wrap(variable), _wrap_bool(isLeft)]
        return _SearchDecision(self, "decisionAbsentIntervalVar", out_params)

    def _decision_present_le(self, variable: IntExpr | int | bool, bound: int | bool, isLeft: bool) -> _SearchDecision:
        out_params: list[_Argument] = [IntExpr._wrap(variable), _wrap_int(bound), _wrap_bool(isLeft)]
        return _SearchDecision(self, "decisionPresentLE", out_params)

    def _decision_optional_gt(self, variable: IntExpr | int | bool, bound: int | bool, isLeft: bool) -> _SearchDecision:
        out_params: list[_Argument] = [IntExpr._wrap(variable), _wrap_int(bound), _wrap_bool(isLeft)]
        return _SearchDecision(self, "decisionOptionalGT", out_params)

    def _decision_present_ge(self, variable: IntExpr | int | bool, bound: int | bool, isLeft: bool) -> _SearchDecision:
        out_params: list[_Argument] = [IntExpr._wrap(variable), _wrap_int(bound), _wrap_bool(isLeft)]
        return _SearchDecision(self, "decisionPresentGE", out_params)

    def _decision_optional_lt(self, variable: IntExpr | int | bool, bound: int | bool, isLeft: bool) -> _SearchDecision:
        out_params: list[_Argument] = [IntExpr._wrap(variable), _wrap_int(bound), _wrap_bool(isLeft)]
        return _SearchDecision(self, "decisionOptionalLT", out_params)

    def _decision_present_start_le(self, variable: IntervalVar, bound: int | bool, isLeft: bool) -> _SearchDecision:
        out_params: list[_Argument] = [IntervalVar._wrap(variable), _wrap_int(bound), _wrap_bool(isLeft)]
        return _SearchDecision(self, "decisionPresentStartLE", out_params)

    def _decision_optional_start_gt(self, variable: IntervalVar, bound: int | bool, isLeft: bool) -> _SearchDecision:
        out_params: list[_Argument] = [IntervalVar._wrap(variable), _wrap_int(bound), _wrap_bool(isLeft)]
        return _SearchDecision(self, "decisionOptionalStartGT", out_params)

    def _decision_present_start_ge(self, variable: IntervalVar, bound: int | bool, isLeft: bool) -> _SearchDecision:
        out_params: list[_Argument] = [IntervalVar._wrap(variable), _wrap_int(bound), _wrap_bool(isLeft)]
        return _SearchDecision(self, "decisionPresentStartGE", out_params)

    def _decision_optional_start_lt(self, variable: IntervalVar, bound: int | bool, isLeft: bool) -> _SearchDecision:
        out_params: list[_Argument] = [IntervalVar._wrap(variable), _wrap_int(bound), _wrap_bool(isLeft)]
        return _SearchDecision(self, "decisionOptionalStartLT", out_params)

    def _decision_present_end_le(self, variable: IntervalVar, bound: int | bool, isLeft: bool) -> _SearchDecision:
        out_params: list[_Argument] = [IntervalVar._wrap(variable), _wrap_int(bound), _wrap_bool(isLeft)]
        return _SearchDecision(self, "decisionPresentEndLE", out_params)

    def _decision_optional_end_gt(self, variable: IntervalVar, bound: int | bool, isLeft: bool) -> _SearchDecision:
        out_params: list[_Argument] = [IntervalVar._wrap(variable), _wrap_int(bound), _wrap_bool(isLeft)]
        return _SearchDecision(self, "decisionOptionalEndGT", out_params)

    def _decision_present_end_ge(self, variable: IntervalVar, bound: int | bool, isLeft: bool) -> _SearchDecision:
        out_params: list[_Argument] = [IntervalVar._wrap(variable), _wrap_int(bound), _wrap_bool(isLeft)]
        return _SearchDecision(self, "decisionPresentEndGE", out_params)

    def _decision_optional_end_lt(self, variable: IntervalVar, bound: int | bool, isLeft: bool) -> _SearchDecision:
        out_params: list[_Argument] = [IntervalVar._wrap(variable), _wrap_int(bound), _wrap_bool(isLeft)]
        return _SearchDecision(self, "decisionOptionalEndLT", out_params)

    def _decision_present_length_le(self, variable: IntervalVar, bound: int | bool, isLeft: bool) -> _SearchDecision:
        out_params: list[_Argument] = [IntervalVar._wrap(variable), _wrap_int(bound), _wrap_bool(isLeft)]
        return _SearchDecision(self, "decisionPresentLengthLE", out_params)

    def _decision_optional_length_gt(self, variable: IntervalVar, bound: int | bool, isLeft: bool) -> _SearchDecision:
        out_params: list[_Argument] = [IntervalVar._wrap(variable), _wrap_int(bound), _wrap_bool(isLeft)]
        return _SearchDecision(self, "decisionOptionalLengthGT", out_params)

    def _no_good(self, decisions: Iterable[_SearchDecision]) -> Constraint:
        out_params: list[_Argument] = [_SearchDecision._wrap_list(decisions)]
        return Constraint(self, "noGood", out_params)

    def _related(self, x: IntervalVar, y: IntervalVar) -> Directive:
        out_params: list[_Argument] = [IntervalVar._wrap(x), IntervalVar._wrap(y)]
        return Directive(self, "related", out_params)

    def pack(self, load: Iterable[IntExpr | int | bool], where: Iterable[IntExpr | int | bool], sizes: Iterable[int | bool]) -> Constraint:
        """#doc[Model.pack]"""
        out_params: list[_Argument] = [IntExpr._wrap_list(load), IntExpr._wrap_list(where), _wrap_int_list(sizes)]
        return Constraint(self, "pack", out_params)


