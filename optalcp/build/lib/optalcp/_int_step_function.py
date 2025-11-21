"""
Integer step function class for OptalCP Python API.
"""

from __future__ import annotations
from collections.abc import Iterable
from typing import Union, TYPE_CHECKING
from ._base_types import ModelElement, _ScalarArgument

if TYPE_CHECKING:
    from ._model import Model
    from ._base_types import _Argument, IntExpr, Constraint, _wrap_int
    from ._interval_var import IntervalVar

class IntStepFunction(ModelElement):
    """
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

