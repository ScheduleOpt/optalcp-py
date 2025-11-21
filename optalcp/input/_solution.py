# Copyright (C) CoEnzyme SAS - All Rights Reserved

"""Solution class for OptalCP."""

from __future__ import annotations
from typing import Any, overload
from ._interval_var import IntervalVar
from ._int_var import IntVar
from ._bool_var import BoolVar


class Solution:
    """#doc[Solution]"""

    def __init__(self) -> None:
        """Create an empty solution where all variables are absent."""
        self._values: dict[int, Any] = {}
        self._objective: float | list[float | None] | None = None

    def get_objective(self) -> float | list[float | None] | None:
        """#doc[Solution.getObjective]"""
        return self._objective

    def is_present(self, variable: IntVar | BoolVar | IntervalVar) -> bool:
        """#doc[Solution.isPresent]"""
        return variable._get_id() in self._values

    def is_absent(self, variable: IntVar | BoolVar | IntervalVar) -> bool:
        """#doc[Solution.isAbsent]"""
        return not variable._get_id() in self._values

    @overload
    def get_value(self, variable: IntVar) -> int | None: ...

    @overload
    def get_value(self, variable: BoolVar) -> bool | None: ...

    @overload
    def get_value(self, variable: IntervalVar) -> tuple[int, int] | None: ...

    def get_value(self, variable: IntVar | BoolVar | IntervalVar) -> int | bool | tuple[int, int] | None:
        """#doc[Solution.getValue]"""

        result = self._values.get(variable._get_id())
        if isinstance(variable, BoolVar):
            # Solver sends bools as 0/1 integers
            return None if result is None else bool(result)
        if not isinstance(variable, (IntVar, IntervalVar)): # type: ignore[misc]
            raise TypeError(f"Expected IntVar, BoolVar, or IntervalVar, got {type(variable).__name__}")
        return result

    def get_start(self, variable: IntervalVar) -> int | None:
        """#doc[Solution.getStart]"""
        if not isinstance(variable, IntervalVar): # type: ignore[misc]
            raise TypeError(f"Expected IntervalVar, got {type(variable).__name__}")

        value = self._values.get(variable._get_id())
        if value is None:
            return None
        return value[0]

    def get_end(self, variable: IntervalVar) -> int | None:
        """#doc[Solution.getEnd]"""
        if not isinstance(variable, IntervalVar): # type: ignore[misc]
            raise TypeError(f"Expected IntervalVar, got {type(variable).__name__}")

        value = self._values.get(variable._get_id())
        if value is None:
            return None
        return value[1]

    def set_objective(self, value: float | None) -> None:
        """#doc[Solution.setObjective]"""
        self._objective = value

    @overload
    def set_value(self, variable: IntVar, value: int) -> None: ...

    @overload
    def set_value(self, variable: BoolVar, value: bool) -> None: ...

    @overload
    def set_value(self, variable: IntervalVar, start: int, end: int) -> None: ...

    def set_value(self, variable: IntVar | BoolVar | IntervalVar, *args: Any) -> None:  # type: ignore[misc]
        """#doc[Solution.setValue]"""
        if isinstance(variable, IntervalVar):
            if len(args) != 2:
                raise ValueError("IntervalVar requires start and end: set_value(var, start, end)")
            start, end = args
            if not isinstance(start, int) or not isinstance(end, int):
                raise TypeError("IntervalVar start and end must be integers")
            self._values[variable._get_id()] = (start, end)
        elif isinstance(variable, BoolVar):
            if len(args) != 1:
                raise ValueError("BoolVar requires a single value: set_value(var, value)")
            value = args[0]
            if not isinstance(value, bool):
                raise TypeError("BoolVar value must be a boolean")
            self._values[variable._get_id()] = value
        elif isinstance(variable, IntVar): # type: ignore[misc]
            if len(args) != 1:
                raise ValueError("IntVar requires a single value: set_value(var, value)")
            value = args[0]
            if not isinstance(value, int):
                raise TypeError("IntVar value must be an integer")
            self._values[variable._get_id()] = value
        else:
            raise TypeError(f"Unknown variable type: {type(variable).__name__}")

    def set_absent(self, variable: IntVar | BoolVar | IntervalVar) -> None:
        """#doc[Solution.setAbsent]"""
        if (not isinstance(variable, (IntVar, BoolVar, IntervalVar))): # type: ignore[misc]
            raise TypeError(f"Expected IntVar, BoolVar, or IntervalVar, got {type(variable).__name__}")

        # Remove from dict entirely
        self._values.pop(variable._get_id(), None)

    def _init_from_dict(self, data: dict[str, Any]) -> None:
        """
        Initialize solution from solver message data.

        Internal method used to deserialize solutions from the solver.

        Args:
            data: Dictionary from solver containing 'values' and 'objective'.
        """
        # Parse values array from solver
        # Format: [{"id": 0, "value": ...}, ...]
        # value can be: null, number (int/bool), or {"start": ..., "end": ...}

        values_list = data.get('values', [])
        for item in values_list:
            var_id = item['id']
            value = item['value']

            if value is None:
                # Absent variable, don't store in dict
                pass
            elif isinstance(value, dict) and 'start' in value:
                # Convert IntervalVar dict to tuple for Pythonic API
                self._values[var_id] = (value['start'], value['end'])
            else:
                # Everything else (None, int, bool) - store as-is
                self._values[var_id] = value

        # Parse objective
        self._objective = data.get('objective')

    def _to_dict(self) -> dict[str, Any]:
        """
        Serialize solution to dictionary for warm start.

        Internal method used to serialize solutions for the solver.

        Returns:
            Dictionary with 'values' and 'objective' keys.
        """
        values_list: list[dict[str, Any]] = []

        for var_id, value in self._values.items():
            if value is None:
                # Absent variable, no need to include it
                pass
            elif isinstance(value, tuple) and len(value) == 2: # type: ignore[misc]
                # IntervalVar - convert tuple to dict
                values_list.append({"id": var_id, "value": {"start": value[0], "end": value[1]}})
            elif isinstance(value, bool):
                # BoolVar - convert to 0/1 for solver
                values_list.append({"id": var_id, "value": 1 if value else 0})
            else:
                # IntVar - store as-is
                values_list.append({"id": var_id, "value": value})

        result: dict[str, Any] = {"values": values_list}
        if self._objective is not None:
            result["objective"] = self._objective

        return result

    def __repr__(self) -> str:
        """String representation of the solution."""
        present_vars = len(self._values)
        obj_str = f", objective={self._objective}" if self._objective is not None else ""
        return f"Solution({present_vars} present{obj_str})"
