"""Pure validation functions for registry value type checking."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .constants import REG_DWORD, REG_EXPAND_SZ, REG_MULTI_SZ, REG_QWORD, REG_SZ

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .types import RegData

_NONE_TYPE = type(None)

_TYPE_ERROR_REG_BINARY = "Objects of type '{data_type}' can not be used as binary registry values"
_TYPE_ERROR_REG_NON_BINARY = "Could not convert the data to the specified type."


def is_list_of_str(list_of_str: Iterable[object]) -> bool:
    """Check whether every element is a string.

    Example:
        >>> is_list_of_str(["a", "b"]), is_list_of_str(["a", 1])
        (True, False)
    """
    return all(isinstance(element, str) for element in list_of_str)


def check_value_type_matches_type(value: RegData, reg_type: int) -> None:
    """Validate that a registry value matches its declared REG_* type.

    The data's EXACT type is compared, not ``isinstance``: ``bool`` is an
    ``int`` subclass that winreg refuses for REG_DWORD/REG_QWORD, and subclasses
    of ``str``/``list``/``bytes`` have always been refused as well.

    Args:
        value: The data to store.
        reg_type: The declared REG_* type.

    Raises:
        ValueError: If a string, integer or multi-string type gets other data.
        TypeError: If a binary (or unknown) type gets data that is not bytes or None.

    Example:
        >>> check_value_type_matches_type(1, REG_DWORD)
        >>> check_value_type_matches_type(True, REG_DWORD)
        Traceback (most recent call last):
            ...
        ValueError: Could not convert the data to the specified type.
    """
    data_type = type(value)

    if reg_type in (REG_SZ, REG_EXPAND_SZ):
        if data_type not in (_NONE_TYPE, str):
            raise ValueError(_TYPE_ERROR_REG_NON_BINARY)

    elif reg_type in (REG_DWORD, REG_QWORD):
        if data_type not in (_NONE_TYPE, int):
            raise ValueError(_TYPE_ERROR_REG_NON_BINARY)

    elif reg_type == REG_MULTI_SZ:
        if data_type not in (_NONE_TYPE, list):
            raise ValueError(_TYPE_ERROR_REG_NON_BINARY)
        if isinstance(value, list) and not is_list_of_str(value):
            raise ValueError(_TYPE_ERROR_REG_NON_BINARY)
    elif data_type not in (_NONE_TYPE, bytes):
        raise TypeError(_TYPE_ERROR_REG_BINARY.format(data_type=data_type.__name__))


__all__ = [
    "check_value_type_matches_type",
    "is_list_of_str",
]
