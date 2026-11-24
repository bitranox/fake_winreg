"""Domain type definitions for registry value data and backend records."""

from __future__ import annotations

from typing import NamedTuple

RegData = None | bytes | int | str | list[str]
"""All possible types of data that registry values can hold."""


class ValueEntry(NamedTuple):
    """One value of a key as a backend enumerates it.

    A NamedTuple so the winreg-facing ``EnumValue`` can still hand callers the
    plain ``(name, data, type)`` tuple the real module returns.

    Example:
        >>> entry = ValueEntry(name="Build", data="19041", value_type=1)
        >>> entry.name, tuple(entry)
        ('Build', ('Build', '19041', 1))
    """

    name: str
    data: RegData
    value_type: int


class KeyInfo(NamedTuple):
    """What a backend reports about one key (``QueryInfoKey``'s three numbers).

    Example:
        >>> KeyInfo(subkey_count=2, value_count=3, last_modified_ns=0).value_count
        3
    """

    subkey_count: int
    value_count: int
    last_modified_ns: int


__all__ = ["KeyInfo", "RegData", "ValueEntry"]
