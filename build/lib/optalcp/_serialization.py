"""
JSON serialization utilities with orjson fallback.
"""

from __future__ import annotations
from typing import Any

# Try to import orjson for fast serialization
try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    import json
    HAS_ORJSON = False # type: ignore[misc]


def serialize_to_json(data: dict[str, Any]) -> bytes:
    """
    Serialize a dictionary to JSON bytes.

    Uses orjson if available (5-10x faster), otherwise falls back to
    standard library json.

    Args:
        data: Dictionary to serialize

    Returns:
        JSON as bytes, suitable for subprocess stdin
    """
    if HAS_ORJSON:
        # Fast path: orjson returns bytes directly
        return orjson.dumps(data) # type: ignore[no-any-return]
    else:
        # Fallback: standard library json returns str, encode to bytes
        return json.dumps(data, separators=(',', ':')).encode('utf-8') # type: ignore[misc]


def is_orjson_available() -> bool:
    """
    Check if orjson is available.

    Returns:
        True if orjson is installed and being used, False otherwise
    """
    return HAS_ORJSON
