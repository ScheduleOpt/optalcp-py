"""
Solver parameters.

Parameters control solver behavior including time limits, search strategies,
number of workers, and worker-specific settings.
"""

from __future__ import annotations
from typing import Optional, Any, Literal # type: ignore[reportUnusedImport]
from dataclasses import dataclass, field, fields

@dataclass(slots=True)
class WorkerParameters:
    """#doc[WorkerParameters]"""

    #include(workerParameters)

    def _to_dict(self) -> dict[str, Any]:
        """Convert set parameters to a dictionary for JSON serialization."""
        return {f.name: getattr(self, f.name) for f in fields(self) if getattr(self, f.name) is not None}

@dataclass(slots=True)
class Parameters:
    """#doc[Parameters]"""

    #include(globalParameters)

    pythonStreamBufferSize: int = field(default=2*1024*1024)
    workers: list[WorkerParameters] = field(default_factory=lambda: [])

    def _to_dict(self) -> dict[str, Any]:
        """Convert to a dictionary for JSON serialization."""
        result = {f.name: getattr(self, f.name) for f in fields(self) if f.name not in ('workers', 'pythonStreamBufferSize') and getattr(self, f.name) is not None}
        if len(self.workers) > 0:
            result['workers'] = [w._to_dict() for w in self.workers]
        return result

    # TODO: _to_dict can be documented function
    # TODO: A function / constructor from dict can be useful (user can have parameters stored in a JSON file).
    # TODO: A copy function can be useful to create modified copies of existing parameters.
