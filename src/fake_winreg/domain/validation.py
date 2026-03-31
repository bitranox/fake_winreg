"""Pure validation functions for registry value type checking."""

from __future__ import annotations

from typing import Any

from .constants import REG_DWORD, REG_EXPAND_SZ, REG_MULTI_SZ, REG_QWORD, REG_SZ
from .types import RegData


def is_list_of_str(list_of_str: list[Any]) -> bool:
    """Check whether every element in the list is a string."""
    return all(isinstance(element, str) for element in list_of_str)


def check_value_type_matches_type(value: RegData, reg_type: int) -> None:
    """Validate that a registry value matches its declared REG_* type.

    Raises TypeError or ValueError if the value doesn't match the type.
    """
    type_error_reg_binary = "Objects of type '{data_type}' can not be used as binary registry values"
    type_error_reg_non_binary = "Could not convert the data to the specified type."
    data_type = type(value).__name__

    if reg_type in (REG_SZ, REG_EXPAND_SZ):
        if data_type not in ("NoneType", "str"):
            raise ValueError(type_error_reg_non_binary)

    elif reg_type in (REG_DWORD, REG_QWORD):
        if data_type not in ("NoneType", "int"):
            raise ValueError(type_error_reg_non_binary)

    elif reg_type == REG_MULTI_SZ:
        if data_type not in ("NoneType", "list"):
            raise ValueError(type_error_reg_non_binary)
        if isinstance(value, list) and not is_list_of_str(value):
            raise ValueError(type_error_reg_non_binary)
    elif data_type not in ("NoneType", "bytes"):
        raise TypeError(type_error_reg_binary.format(data_type=data_type))


__all__ = [
    "check_value_type_matches_type",
    "is_list_of_str",
]
