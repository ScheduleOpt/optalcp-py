"""
Shared utilities for solver communication.

This module contains internal utility functions used by both sync and async
solver implementations. These are not part of the public API.
"""

from __future__ import annotations

import os
import sys
from typing import IO


def _enable_windows_ansi() -> bool:
    """
    Enable ANSI escape sequences on Windows.

    Returns:
        True if ANSI mode was enabled or already supported, False otherwise
    """
    if sys.platform != 'win32':
        return True  # Not Windows, assume ANSI is supported

    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # Get handle to stdout
        handle = kernel32.GetStdHandle(-11)
        # Enable VIRTUAL_TERMINAL_PROCESSING (0x0004) | DISABLE_NEWLINE_AUTO_RETURN (0x0008)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            mode.value |= 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
            return bool(kernel32.SetConsoleMode(handle, mode))
    except Exception:
        pass

    return False


def _can_use_colors(output_stream: IO[str] | None) -> bool:
    """
    Detect if ANSI color codes can be used in output.

    Checks multiple conditions to determine color support:
    - NO_COLOR environment variable (disables colors if set)
    - FORCE_COLOR environment variable (forces colors if set)
    - Jupyter/IPython environments (VS Code notebooks, JupyterLab, etc.)
    - TTY detection for terminal output
    - Windows ANSI support

    Args:
        output_stream: The output stream to check (e.g., sys.stdout)

    Returns:
        True if ANSI colors can be used, False otherwise

    References:
        - NO_COLOR standard: https://no-color.org/
        - FORCE_COLOR: Common convention for CI/CD and logging
    """
    # Respect NO_COLOR standard: https://no-color.org/
    if os.environ.get('NO_COLOR'):
        return False

    # Force colors if requested (useful for CI/CD, logging)
    if os.environ.get('FORCE_COLOR'):
        return True

    # No stream = no colors
    if output_stream is None:
        return False

    # Detect Jupyter/IPython environments (VS Code notebooks, JupyterLab, Jupyter Classic, etc.)
    # These environments support ANSI colors even though they're not TTYs
    # IPython injects get_ipython() into the global namespace when running in a kernel
    get_ipython_func = globals().get('get_ipython')
    if get_ipython_func is not None and get_ipython_func() is not None:
        # We're running in a Jupyter kernel - colors work!
        return True

    # Check if output stream is a TTY (traditional terminal check)
    if hasattr(output_stream, 'isatty') and output_stream.isatty():
        # On Windows, try to enable ANSI support
        if sys.platform == 'win32':
            return _enable_windows_ansi()
        return True

    # No color support detected
    return False


def _find_solver_path() -> str:
    """
    Find the path to the optalcp solver executable.

    Checks in order:
    1. OPTALCP_SOLVER environment variable (override)
    2. optalcp-bin package (full edition) - priority 1
    3. optalcp-bin-academic package - priority 2
    4. optalcp-bin-preview package - priority 3
    5. optalcp in PATH

    Returns:
        Path to the solver executable

    Raises:
        FileNotFoundError: If solver cannot be found

    Remarks:
        This function mirrors the JavaScript solver discovery logic from
        npm-packages/optalcp/input/api.ts:2045-2067. If multiple binary
        packages are installed, the full edition takes priority over academic,
        which takes priority over preview.
    """
    # 1. Check environment variable first (override)
    solver_path = os.environ.get('OPTALCP_SOLVER')
    if solver_path:
        if os.path.isfile(solver_path) and os.access(solver_path, os.X_OK):
            return solver_path
        else:
            raise FileNotFoundError(
                f"OPTALCP_SOLVER points to invalid executable: {solver_path}"
            )

    # 2. Try optalcp-bin (full edition) - priority 1
    try:
        import optalcp_bin  # type: ignore[import]
        return str(optalcp_bin.get_solver_path())
    except ImportError:
        pass
    except Exception:
        pass  # Binary not available for this platform

    # 3. Try optalcp-bin-academic - priority 2
    try:
        import optalcp_bin_academic  # type: ignore[import]
        return str(optalcp_bin_academic.get_solver_path())
    except ImportError:
        pass
    except Exception:
        pass

    # 4. Try optalcp-bin-preview - priority 3
    try:
        import optalcp_bin_preview  # type: ignore[import]
        return str(optalcp_bin_preview.get_solver_path())
    except ImportError:
        pass
    except Exception:
        pass

    # 5. Try to find optalcp in PATH
    import shutil
    solver_path = shutil.which('optalcp')
    if solver_path:
        return solver_path

    # Not found
    raise FileNotFoundError(
        "OptalCP solver not found. Install with:\n"
        "  pip install git+https://github.com/ScheduleOpt/optalcp-py-bin-preview@latest\n"
        "Or set OPTALCP_SOLVER environment variable, or ensure 'optalcp' is in your PATH."
    )
