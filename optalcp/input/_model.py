"""
Core model classes for OptalCP Python API.
"""

from __future__ import annotations
from collections.abc import Iterable
from typing import Any
from ._base_types import *
from ._base_types import _wrap_int, _wrap_int_list, _wrap_bool, _wrap_int_matrix, Directive, _SearchDecision, _ScalarArgument, _Argument, _ElementProps, _PresenceStatus # type: ignore[reportUnusedImport]
from ._int_var import IntVar
from ._bool_var import BoolVar
from ._interval_var import IntervalVar
from ._sequence_var import SequenceVar
from ._int_step_function import IntStepFunction
from ._parameters import Parameters


class Model:
    """#doc[Model]"""

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
        self._objective: dict[str, Any] | None = None
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

    def interval_var(self,
                     start: tuple[int, int] | None = None,
                     end: tuple[int, int] | None = None,
                     length: int | tuple[int, int] | None = None,
                     optional: bool = False,
                     name: str | None = None) -> IntervalVar:
        """#doc[Model.intervalVar]"""
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
        """#doc[Model.intVar]"""
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
                     types: Iterable[int] | None = None) -> SequenceVar:
        """#doc[Model.sequenceVar]"""
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
        """#doc[Model.stepFunction]"""
        return IntStepFunction(self, values)

    def constraint(self, constraint: Constraint | BoolExpr | bool) -> None:
        """#doc[Model.constraint]"""
        if not isinstance(constraint, Constraint):
            self._model.append(BoolExpr._wrap(constraint))

    def minimize(self, expr: IntExpr | int) -> None:
        """#doc[Model.minimize]"""
        self._objective = {
            'func': 'minimize',
            'args': [IntExpr._wrap(expr)]
        }

    def maximize(self, expr: IntExpr | int) -> None:
        """#doc[Model.maximize]"""
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

    def sum(self, args: Iterable[IntExpr | int | bool] | Iterable[CumulExpr]) -> IntExpr | int | CumulExpr:
        """#doc[Model.sum]"""

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

    #include(modelMethods)
