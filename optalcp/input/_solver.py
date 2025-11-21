"""
Solver communication and execution.

This module provides the simple synchronous solve() function for basic usage.
For advanced usage with event callbacks and async support, use the Solver class
from _async_solver module.
"""

from __future__ import annotations
import asyncio
import nest_asyncio  # type: ignore[import-untyped]
from collections.abc import Sequence
from typing import Any, final
from typing_extensions import TypedDict
from ._model import Model
from ._solution import Solution
from ._parameters import Parameters


def _has_running_loop() -> bool:
    """Check if there's a running event loop."""
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


@final
class ObjectiveEntry(TypedDict, total=False):
    """
    Single entry in the objective value history.

    Tracks when each improving solution was found during the solve,
    along with its objective value and validation status.
    """
    solveTime: float
    """Duration of the solve when this solution was found, in seconds."""

    objective: float | list[float | None]
    """The objective value of this solution."""

    valid: bool
    """Whether this solution was verified (if verification is enabled)."""


@final
class LowerBoundEntry(TypedDict):
    """
    Single entry in the lower bound history.

    Tracks when a new (better) lower bound on the objective was proved,
    along with the solve time and bound value.
    """
    solveTime: float
    """Duration of the solve at the time the lower bound was found, in seconds."""

    value: float | list[float | None]
    """The new lower bound value (single float or list for multi-objective)."""


class SolveResult:
    """#doc[SolveResult]"""

    def __init__(self, data: dict[str, Any],
                 best_solution: Solution | None = None,
                 solutions: list[Solution] | None = None,
                 objective_history: list[ObjectiveEntry] | None = None,
                 lower_bound_history: list[LowerBoundEntry] | None = None,
                 best_solution_time: float | None = None,
                 best_lb_time: float | None = None,
                 best_solution_valid: bool | None = None):
        """
        Create a solve result from solver response data.

        Args:
            data: Dictionary containing solve results (SolveSummary)
            best_solution: The best solution found (if any)
            solutions: All solutions found (if stored)
            objective_history: History of objective improvements
            lower_bound_history: History of lower bound improvements
            best_solution_time: Time when best solution was found
            best_lb_time: Time of last lower bound improvement
            best_solution_valid: Whether best solution was verified
        """
        self._data = data
        self._best_solution = best_solution
        self._solutions = solutions if solutions is not None else []
        self._objective_history = objective_history if objective_history is not None else []
        self._lower_bound_history = lower_bound_history if lower_bound_history is not None else []
        self._best_solution_time = best_solution_time
        self._best_lb_time = best_lb_time
        self._best_solution_valid = best_solution_valid

    @property
    def nb_solutions(self) -> int:
        """Number of solutions found during the solve."""
        return self._data.get('nbSolutions', 0)

    @property
    def proof(self) -> bool:
        """Whether the solve ended with a proof (optimality or infeasibility)."""
        return self._data.get('proof', False)

    @property
    def duration(self) -> float:
        """Total duration of the solve in seconds."""
        return self._data.get('duration', 0.0)

    @property
    def nb_branches(self) -> int:
        """Total number of branches during the solve."""
        return self._data.get('nbBranches', 0)

    @property
    def nb_fails(self) -> int:
        """Total number of fails during the solve."""
        return self._data.get('nbFails', 0)

    @property
    def objective_value(self) -> float | None:
        """Objective value of the best solution found, or None if no solution."""
        return self._data.get('objective')

    @property
    def lower_bound(self) -> float | None:
        """Lower bound proved by the solver, or None if no bound proved."""
        return self._data.get('lowerBound')

    @property
    def best_solution(self) -> Solution | None:
        """
        The best solution found during the solve.

        Returns:
            The best solution, or None if no solution was found.
        """
        return self._best_solution

    @property
    def solutions(self) -> Sequence[Solution]:
        """
        All solutions found during the solve.

        Returns:
            List of all solutions. Empty list if no solutions were found.
            Note: Solutions are only stored if specifically requested via parameters.
        """
        return self._solutions

    # Additional SolveSummary fields
    @property
    def nb_lns_steps(self) -> int:
        """Total number of Large Neighborhood Search steps."""
        return self._data.get('nbLNSSteps', 0)

    @property
    def nb_restarts(self) -> int:
        """Total number of restarts performed."""
        return self._data.get('nbRestarts', 0)

    @property
    def memory_used(self) -> int:
        """Memory used by the solver in bytes."""
        return self._data.get('memoryUsed', 0)

    @property
    def nb_int_vars(self) -> int:
        """Number of integer variables in the model (after preprocessing)."""
        return self._data.get('nbIntVars', 0)

    @property
    def nb_interval_vars(self) -> int:
        """Number of interval variables in the model (after preprocessing)."""
        return self._data.get('nbIntervalVars', 0)

    @property
    def nb_constraints(self) -> int:
        """Number of constraints in the model (after preprocessing)."""
        return self._data.get('nbConstraints', 0)

    @property
    def solver(self) -> str:
        """Solver name and version string (e.g., 'OptalCP 2025.8.0')."""
        return self._data.get('solver', '')

    @property
    def nb_workers(self) -> int:
        """Number of worker threads used during solving."""
        return self._data.get('nbWorkers', 0)

    @property
    def cpu(self) -> str:
        """CPU name detected by the solver."""
        return self._data.get('cpu', '')

    @property
    def objective_sense(self) -> str | None:
        """Objective direction: 'minimize', 'maximize', or None for satisfaction problems."""
        return self._data.get('objectiveSense')

    # Tracking data (beyond SolveSummary)
    @property
    def objective_history(self) -> Sequence[ObjectiveEntry]:
        """
        History of objective value improvements during the solve.

        Each entry contains: solveTime, objective, valid
        """
        return self._objective_history

    @property
    def lower_bound_history(self) -> Sequence[LowerBoundEntry]:
        """
        History of lower bound improvements during the solve.

        Each entry contains: solveTime, value
        """
        return self._lower_bound_history

    @property
    def best_solution_time(self) -> float | None:
        """Time when the best solution was found, in seconds."""
        return self._best_solution_time

    @property
    def best_lb_time(self) -> float | None:
        """Time of the last lower bound improvement, in seconds."""
        return self._best_lb_time

    @property
    def best_solution_valid(self) -> bool | None:
        """Whether the best solution was verified (if verification enabled)."""
        return self._best_solution_valid

    def __repr__(self) -> str:
        if self.nb_solutions > 0:
            obj_str = f", objective={self.objective_value}" if self.objective_value is not None else ""
            return f"<SolveResult: {self.nb_solutions} solution(s){obj_str}, duration={self.duration:.2f}s>"
        else:
            return f"<SolveResult: no solution, proof={self.proof}, duration={self.duration:.2f}s>"


# TODO-MISSING-DOC-FILE: solve.md needs to be created (function exists in JavaScript but not documented)
def solve(model: Model,
          params: Parameters | None = None,
          warm_start: Solution | None = None) -> SolveResult:
    """
    Solve a model (simple synchronous version).

    This is a simple blocking function for basic usage. For advanced features like
    event callbacks, progress monitoring, or async support, use the Solver class instead.

    This function works seamlessly in both regular Python scripts and Jupyter notebooks.
    In Jupyter (where an event loop is already running), it automatically applies
    nest_asyncio to allow nested event loops.

    Example:
        result = solve(model)
        print(f"Objective: {result.objective_value}")

    Example with Parameters:
        from optalcp import Parameters

        params = Parameters()
        params.time_limit = 60
        params.search_type = "LNS"
        result = solve(model, params)

    For advanced usage:
        from optalcp import Solver

        solver = Solver(on_log=print)
        result = await solver.solve(model)

    Args:
        model: The model to solve
        params: Parameters object with solver settings (optional)
        warm_start: Initial solution to start search from (optional)

    Returns:
        SolveResult with information about the solve

    Raises:
        FileNotFoundError: If solver executable cannot be found
        RuntimeError: If solver fails or returns an error
    """
    from ._async_solver import Solver

    # Use Solver class internally
    solver = Solver()

    # Check if we're in an async context (e.g., Jupyter notebook)
    if _has_running_loop():
        # Apply nest_asyncio to allow nested event loops
        nest_asyncio.apply()  # type: ignore

    return asyncio.run(solver.solve(model, params=params, warm_start=warm_start))
