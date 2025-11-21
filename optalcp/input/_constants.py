"""
Constants for the OptalCP package.
"""

from __future__ import annotations
from enum import IntEnum

# Maximum value of a decision variable or a decision expression
IntVarMax = 1073741823

# Minimum value of a decision variable or a decision expression
IntVarMin = -IntVarMax

# Maximum value of start or end of an interval variable
IntervalMax = 715827882

# Minimum value of start or end of an interval variable
IntervalMin = -IntervalMax

# Maximum length of an interval variable
LengthMax = IntervalMax - IntervalMin

# Presence status values (synchronized with C++ enum Presence::Value)
# Internal - use is_optional(), is_present(), is_absent() methods instead
class _PresenceStatus(IntEnum):
    Optional = 0
    Present = 1
    Absent = 2
