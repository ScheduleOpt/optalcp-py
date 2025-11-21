"""
OptalCP Python API

A Pythonic interface to the OptalCP constraint programming solver.
"""

from __future__ import annotations

__version__: str = '2025.11.1'

# Import main classes
from ._model import (
    Model as Model,
    ModelElement as ModelElement,
    IntVar as IntVar,
    BoolVar as BoolVar,
    IntervalVar as IntervalVar,
    IntExpr as IntExpr,
    BoolExpr as BoolExpr,
    Constraint as Constraint,
    CumulExpr as CumulExpr,
    SequenceVar as SequenceVar,
    IntStepFunction as IntStepFunction,
)

# Import constants
from ._constants import (
    IntVarMax as IntVarMax,
    IntVarMin as IntVarMin,
    IntervalMax as IntervalMax,
    IntervalMin as IntervalMin,
    LengthMax as LengthMax,
)

# Import parameters
from ._parameters import Parameters as Parameters, WorkerParameters as WorkerParameters

# Import solver
from ._solver import (
    solve as solve,
    SolveResult as SolveResult,
    ObjectiveEntry as ObjectiveEntry,
    LowerBoundEntry as LowerBoundEntry,
)
from ._async_solver import (
    Solver as Solver,
    SolutionEvent as SolutionEvent,
    SolveSummary as SolveSummary,
)
from ._solution import Solution as Solution

# Import utilities
from ._serialization import is_orjson_available as is_orjson_available

__all__: list[str] = [
    # Main classes
    'Model',
    'ModelElement',
    'IntVar',
    'BoolVar',
    'IntervalVar',
    'IntExpr',
    'BoolExpr',
    'Constraint',
    'CumulExpr',
    'SequenceVar',
    'IntStepFunction',
    # Constants
    'IntVarMax',
    'IntVarMin',
    'IntervalMax',
    'IntervalMin',
    'LengthMax',
    # Parameters
    'Parameters',
    'WorkerParameters',
    # Solver
    'solve',
    'Solver',
    'SolveResult',
    'Solution',
    'SolutionEvent',
    'ObjectiveEntry',
    'LowerBoundEntry',
    'SolveSummary',
    # Utilities
    'is_orjson_available',
]
