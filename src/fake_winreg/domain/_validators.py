"""Winreg-compatible argument validation helpers.

Extracted from api.py to keep the public API module focused on
registry operations. These mirror the validation behavior of the
real Windows winreg module.
"""

from __future__ import annotations

import inspect
from typing import Any

from .handles import PyHKEY


def check_key(key: Any) -> None:
    """Validate a registry key handle."""
    if key is None:
        raise TypeError("None is not a valid HKEY in this context")
    if not isinstance(key, (int, PyHKEY)):
        raise TypeError("The object is not a PyHKEY object")
    if isinstance(key, int) and key >= 2**64:
        raise OverflowError("int too big to convert")


def check_index(index: Any) -> None:
    """Validate an integer index (also used for access masks)."""
    index_type = type(index).__name__
    if not isinstance(index, int):
        raise TypeError(f"an integer is required (got type {index_type})")
    elif index >= 2**64:
        raise OverflowError("Python int too large to convert to C long")


def check_access(access: Any) -> None:
    """Validate an access mask (same rules as index)."""
    check_index(access)


def check_reserved(reserved: Any) -> None:
    """Validate a reserved parameter (must be 0)."""
    check_access(reserved)
    if isinstance(reserved, int) and reserved != 0:
        error = OSError("[WinError 87] The parameter is incorrect")
        error.winerror = 87  # type: ignore[attr-defined]
        raise error


def check_reserved2(reserved: Any) -> None:
    """Validate reserved parameter for OpenKey (allows 0-3)."""
    if isinstance(reserved, int) and 3 < reserved < 2**64:
        raise_permission_error()
    check_access(reserved)


def check_argument_must_be_type_expected(arg_number: int, argument: Any, type_expected: type) -> None:
    """Validate argument type, raising TypeError with caller's function name."""
    function_name = inspect.stack()[1].function
    if not isinstance(argument, type_expected):
        argument_type = type(argument).__name__
        if argument_type == "NoneType":
            argument_type = "None"
        raise TypeError(
            f"{function_name}() argument {arg_number} must be {type_expected.__name__}, not {argument_type}"
        )


def check_argument_must_be_str_or_none(arg_number: int, argument: Any) -> None:
    """Validate argument is str or None, raising TypeError with caller's function name."""
    function_name = inspect.stack()[1].function
    if not isinstance(argument, str) and argument is not None:
        subkey_type = type(argument).__name__
        raise TypeError(f"{function_name}() argument {arg_number} must be str or None, not {subkey_type}")


def raise_permission_error() -> None:
    """Raise PermissionError with WinError 5."""
    permission_error = PermissionError("[WinError 5] Access is denied")
    permission_error.winerror = 5  # type: ignore[attr-defined]
    raise permission_error


def raise_os_error_1010() -> None:
    """Raise OSError with WinError 1010 (invalid registry key)."""
    error = OSError("[WinError 1010] The configuration registry key is invalid")
    error.winerror = 1010  # type: ignore[attr-defined]
    raise error
