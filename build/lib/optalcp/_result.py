"""
Result type definitions.

This module provides type definitions for solve results and summaries.
The actual solving implementation is in _solver.py (Solver class).
"""

from __future__ import annotations
import json
from collections.abc import Sequence
from typing import final
from typing_extensions import TypedDict, NotRequired
from ._model import Model
from ._solution import Solution
from ._parameters import Parameters


@final
class ObjectiveEntry(TypedDict):
    """
    Single entry in the objective value history.

    Tracks when each improving solution was found during the solve,
    along with its objective value and validation status.
    """
    solveTime: float
    """Duration of the solve when this solution was found, in seconds."""

    objective: float | None
    """The objective value of this solution."""

    valid: NotRequired[bool]
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

    value: float
    """The new lower bound value."""


@final
class ProblemDefinition(TypedDict):
    r"""
    The definition of a problem to solve, i.e., all the input the solver needs for solving.

    This type contains everything that is needed to solve a model. In particular
    it contains the model itself, the parameters to use for solving (optional)
    and the starting solution (optional).
    """
    model: Model
    parameters: NotRequired[Parameters]
    warm_start: NotRequired[Solution]


@final
class _RawSolveSummary(TypedDict):
    """
    Internal: Raw summary statistics from solver (camelCase wire format).
0
    This matches the JSON format from the solver and is used internally.
    Users receive the snake_case SolveSummary version instead.

    Most fields are required, matching TypeScript SolveSummary.
    Only objective, lowerBound, and objectiveSense are optional.
    """
    # Core results (required)
    nbSolutions: int
    proof: bool
    duration: float

    # Search statistics (required)
    nbBranches: int
    nbFails: int
    nbLNSSteps: int
    nbRestarts: int

    # Resource usage (required)
    memoryUsed: int

    # Objective information (optional - only present for optimization problems)
    objective: NotRequired[float]
    lowerBound: NotRequired[float]
    objectiveSense: NotRequired[str]

    # Model statistics (required)
    nbIntVars: int
    nbIntervalVars: int
    nbConstraints: int

    # Environment information (required)
    solver: str
    nbWorkers: int
    cpu: str


@final
class SolveSummary:
    """
    Summary statistics from the solver at completion.

    Passed to the on_summary callback with snake_case property access.
    For a richer interface with additional tracking data, see SolveResult.

    All fields are optional as the exact set of fields may vary depending
    on solver version and problem type.
    """

    def __init__(self, data: _RawSolveSummary):
        """
        Create a solve summary from raw solver data.

        Args:
            data: Raw summary dict with camelCase keys from the solver.
        """
        self._data = data

    # Core results (required fields)
    @property
    def nb_solutions(self) -> int:
        """Total number of solutions found."""
        return self._data['nbSolutions']

    @property
    def proof(self) -> bool:
        """Whether the solve ended with a proof (optimality or infeasibility)."""
        return self._data['proof']

    @property
    def duration(self) -> float:
        """Total duration of the solve in seconds."""
        return self._data['duration']

    # Search statistics (required fields)
    @property
    def nb_branches(self) -> int:
        """Total number of branches explored."""
        return self._data['nbBranches']

    @property
    def nb_fails(self) -> int:
        """Total number of failures encountered."""
        return self._data['nbFails']

    @property
    def nb_lns_steps(self) -> int:
        """Total number of Large Neighborhood Search steps."""
        return self._data['nbLNSSteps']

    @property
    def nb_restarts(self) -> int:
        """Total number of restarts performed."""
        return self._data['nbRestarts']

    # Resource usage (required field)
    @property
    def memory_used(self) -> int:
        """Memory used by the solver in bytes."""
        return self._data['memoryUsed']

    # Objective information (optional fields)
    @property
    def objective(self) -> float | None:
        """Best objective value found (for optimization problems)."""
        return self._data.get('objective')

    @property
    def lower_bound(self) -> float | None:
        """Proved lower bound on the objective (for minimization problems)."""
        return self._data.get('lowerBound')

    @property
    def objective_sense(self) -> str | None:
        """Objective direction: 'minimize', 'maximize', or None for satisfaction problems."""
        return self._data.get('objectiveSense')

    # Model statistics (required fields)
    @property
    def nb_int_vars(self) -> int:
        """Number of integer variables in the model (after preprocessing)."""
        return self._data['nbIntVars']

    @property
    def nb_interval_vars(self) -> int:
        """Number of interval variables in the model (after preprocessing)."""
        return self._data['nbIntervalVars']

    @property
    def nb_constraints(self) -> int:
        """Number of constraints in the model (after preprocessing)."""
        return self._data['nbConstraints']

    # Environment information (required fields)
    @property
    def solver(self) -> str:
        """Solver name and version string (e.g., 'OptalCP 2025.8.0')."""
        return self._data['solver']

    @property
    def nb_workers(self) -> int:
        """Number of worker threads used during solving."""
        return self._data['nbWorkers']

    @property
    def cpu(self) -> str:
        """CPU name detected by the solver."""
        return self._data['cpu']

    def __repr__(self) -> str:
        if self.nb_solutions > 0:
            obj_str = f", objective={self.objective}" if self.objective is not None else ""
            return f"<SolveSummary: {self.nb_solutions} solution(s){obj_str}, duration={self.duration:.2f}s>"
        else:
            return f"<SolveSummary: no solution, proof={self.proof}, duration={self.duration:.2f}s>"


class SolveResult:
    """#doc[SolveResult]

    Complete solve result with summary statistics and solution data.

    Provides all fields from SolveSummary plus additional tracking data:
    - solution: The best solution found
    - solutions: All solutions (if stored)
    - objective_history, lower_bound_history: Tracking data
    - Timestamps for solutions and bounds

    This is the primary result type returned by solve() and Solver.solve().
    """

    def __init__(self, data: _RawSolveSummary,
                 solution: Solution | None = None,
                 solutions: list[Solution] | None = None,
                 objective_history: list[ObjectiveEntry] | None = None,
                 lower_bound_history: list[LowerBoundEntry] | None = None,
                 solution_time: float | None = None,
                 best_lb_time: float | None = None,
                 solution_valid: bool | None = None):
        """
        Create a solve result from solver response data.

        Args:
            data: Raw summary statistics (camelCase dict from solver)
            solution: The best solution found (if any)
            solutions: All solutions found (if stored)
            objective_history: History of objective improvements
            lower_bound_history: History of lower bound improvements
            solution_time: Time when best solution was found
            best_lb_time: Time of last lower bound improvement
            solution_valid: Whether best solution was verified
        """
        self._data = data
        self._solution = solution
        self._solutions = solutions if solutions is not None else []
        self._objective_history = objective_history if objective_history is not None else []
        self._lower_bound_history = lower_bound_history if lower_bound_history is not None else []
        self._solution_time = solution_time
        self._best_lb_time = best_lb_time
        self._solution_valid = solution_valid

    @property
    def nb_solutions(self) -> int:
        """Number of solutions found during the solve."""
        return self._data['nbSolutions']

    @property
    def proof(self) -> bool:
        """Whether the solve ended with a proof (optimality or infeasibility)."""
        return self._data['proof']

    @property
    def duration(self) -> float:
        """Total duration of the solve in seconds."""
        return self._data['duration']

    @property
    def nb_branches(self) -> int:
        """Total number of branches during the solve."""
        return self._data['nbBranches']

    @property
    def nb_fails(self) -> int:
        """Total number of fails during the solve."""
        return self._data['nbFails']

    @property
    def objective_value(self) -> float | None:
        """Objective value of the best solution found, or None if no solution."""
        return self._data.get('objective')

    @property
    def objective(self) -> float | None:
        """Alias for objective_value (matches SolveSummary field name)."""
        return self._data.get('objective')

    @property
    def lower_bound(self) -> float | None:
        """Lower bound proved by the solver, or None if no bound proved."""
        return self._data.get('lowerBound')

    @property
    def solution(self) -> Solution | None:
        """
        The best solution found during the solve.

        Returns:
            The best solution, or None if no solution was found.
        """
        return self._solution

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
        return self._data['nbLNSSteps']

    @property
    def nb_restarts(self) -> int:
        """Total number of restarts performed."""
        return self._data['nbRestarts']

    @property
    def memory_used(self) -> int:
        """Memory used by the solver in bytes."""
        return self._data['memoryUsed']

    @property
    def nb_int_vars(self) -> int:
        """Number of integer variables in the model (after preprocessing)."""
        return self._data['nbIntVars']

    @property
    def nb_interval_vars(self) -> int:
        """Number of interval variables in the model (after preprocessing)."""
        return self._data['nbIntervalVars']

    @property
    def nb_constraints(self) -> int:
        """Number of constraints in the model (after preprocessing)."""
        return self._data['nbConstraints']

    @property
    def solver(self) -> str:
        """Solver name and version string (e.g., 'OptalCP 2025.8.0')."""
        return self._data['solver']

    @property
    def nb_workers(self) -> int:
        """Number of worker threads used during solving."""
        return self._data['nbWorkers']

    @property
    def cpu(self) -> str:
        """CPU name detected by the solver."""
        return self._data['cpu']

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
    def solution_time(self) -> float | None:
        """Time when the best solution was found, in seconds."""
        return self._solution_time

    @property
    def best_lb_time(self) -> float | None:
        """Time of the last lower bound improvement, in seconds."""
        return self._best_lb_time

    @property
    def solution_valid(self) -> bool | None:
        """Whether the best solution was verified (if verification enabled)."""
        return self._solution_valid

    def __repr__(self) -> str:
        if self.nb_solutions > 0:
            obj_str = f", objective={self.objective_value}" if self.objective_value is not None else ""
            return f"<SolveResult: {self.nb_solutions} solution(s){obj_str}, duration={self.duration:.2f}s>"
        else:
            return f"<SolveResult: no solution, proof={self.proof}, duration={self.duration:.2f}s>"


def _to_json_impl(model: Model,
                  params: Parameters | None = None,
                  warm_start: Solution | None = None) -> str:
    """Internal implementation for Model.to_json()."""
    model_data = model._to_dict()

    if params is not None:
        model_data['parameters'] = params._to_dict()

    if warm_start is not None:
        model_data['warmStart'] = warm_start._to_dict()  # JSON uses camelCase

    # Return string (not bytes) for easier file writing
    return json.dumps(model_data)


def _from_json_impl(json_str: str) -> tuple[Model, Parameters | None, Solution | None]:
    """Internal implementation for Model.from_json()."""
    data = json.loads(json_str)

    # Deserialize model
    model = Model()
    model._from_dict(data)

    # Deserialize parameters if present
    params: Parameters | None = None
    if 'parameters' in data:
        params = Parameters()
        params._from_dict(data['parameters'])

    # Deserialize warm start if present
    warm_start: Solution | None = None
    if 'warmStart' in data:
        warm_start = Solution()
        warm_start._init_from_dict(data['warmStart'])

    return (model, params, warm_start)
