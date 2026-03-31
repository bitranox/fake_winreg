"""Core registry data structures and operations.

Provides the in-memory representation of a Windows registry: hives, keys,
and values, plus functions to create and retrieve them.
"""

from __future__ import annotations

import time

from .constants import (
    HKEY_CLASSES_ROOT,
    HKEY_CURRENT_CONFIG,
    HKEY_CURRENT_USER,
    HKEY_DYN_DATA,
    HKEY_LOCAL_MACHINE,
    HKEY_PERFORMANCE_DATA,
    HKEY_USERS,
    KEY_READ,
    REG_SZ,
)
from .types import RegData


class FakeRegistry:
    """Container for the entire fake Windows registry."""

    def __init__(self) -> None:
        self.hive: dict[object, FakeRegistryKey] = {}
        self.hive[HKEY_CLASSES_ROOT] = set_fake_reg_key(FakeRegistryKey(), "HKEY_CLASSES_ROOT")
        self.hive[HKEY_CURRENT_CONFIG] = set_fake_reg_key(FakeRegistryKey(), "HKEY_CURRENT_CONFIG")
        self.hive[HKEY_CURRENT_USER] = set_fake_reg_key(FakeRegistryKey(), "HKEY_CURRENT_USER")
        self.hive[HKEY_DYN_DATA] = set_fake_reg_key(FakeRegistryKey(), "HKEY_DYN_DATA")
        self.hive[HKEY_LOCAL_MACHINE] = set_fake_reg_key(FakeRegistryKey(), "HKEY_LOCAL_MACHINE")
        self.hive[HKEY_PERFORMANCE_DATA] = set_fake_reg_key(FakeRegistryKey(), "HKEY_PERFORMANCE_DATA")
        self.hive[HKEY_USERS] = set_fake_reg_key(FakeRegistryKey(), "HKEY_USERS")


class FakeRegistryKey:
    """Represents a single registry key (folder) in the fake registry.

    >>> fake_reg_root = FakeRegistryKey()
    """

    def __init__(self) -> None:
        self.full_key: str = ""
        self.parent_fake_registry_key: FakeRegistryKey | None = None
        self.subkeys: dict[str, FakeRegistryKey] = {}
        self.values: dict[str, FakeRegistryValue] = {}
        self.last_modified_ns: int = 0


class FakeRegistryValue:
    """Represents a single registry value (data item) within a key.

    >>> fake_reg_value = FakeRegistryValue()
    """

    def __init__(self) -> None:
        self.full_key: str = ""
        self.value_name: str = ""
        self.value: RegData = ""
        self.value_type: int = REG_SZ
        self.access: int = KEY_READ
        self.last_modified_ns: int | None = None


def set_fake_reg_key(
    fake_reg_key: FakeRegistryKey,
    sub_key: str | None = None,
    last_modified_ns: int | None = None,
) -> FakeRegistryKey:
    r"""Create a registry key if it does not already exist.

    Automatically creates intermediate parent keys as needed.

    >>> fake_reg_root = FakeRegistryKey()
    >>> key = set_fake_reg_key(fake_reg_key=fake_reg_root, sub_key='HKEY_LOCAL_MACHINE')
    >>> assert key.full_key == 'HKEY_LOCAL_MACHINE'
    >>> result = set_fake_reg_key(
    ...     fake_reg_key=fake_reg_root,
    ...     sub_key=r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT',
    ... )
    >>> assert result.full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT'
    """
    if last_modified_ns is None:
        last_modified_ns = get_windows_timestamp_now()

    key_parts_full = fake_reg_key.full_key.split("\\")
    key_parts_sub = sub_key.split("\\") if sub_key else []

    data = fake_reg_key
    for key_part in key_parts_sub:
        key_parts_full.append(key_part)
        if key_part not in data.subkeys:
            data.subkeys[key_part] = FakeRegistryKey()
            data.subkeys[key_part].full_key = "\\".join(key_parts_full).strip("\\")
            data.subkeys[key_part].last_modified_ns = last_modified_ns
            data.subkeys[key_part].parent_fake_registry_key = data
        data = data.subkeys[key_part]

    return data


def get_fake_reg_key(fake_reg_key: FakeRegistryKey, sub_key: str) -> FakeRegistryKey:
    r"""Retrieve an existing registry key by path.

    Raises FileNotFoundError if the key does not exist.

    >>> fake_reg_root = FakeRegistryKey()
    >>> _ = set_fake_reg_key(fake_reg_key=fake_reg_root,
    ...     sub_key=r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT')

    >>> result = get_fake_reg_key(fake_reg_key=fake_reg_root,
    ...     sub_key=r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT')
    >>> assert result.full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT'

    >>> get_fake_reg_key(  # doctest: +ELLIPSIS
    ...     fake_reg_key=fake_reg_root,
    ...     sub_key=r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\non_existing',
    ... )
    Traceback (most recent call last):
        ...
    FileNotFoundError: subkey not found, ...
    """
    current_fake_reg_key = fake_reg_key
    if sub_key:
        key_parts = sub_key.split("\\")
        for key_part in key_parts:
            try:
                current_fake_reg_key = current_fake_reg_key.subkeys[key_part]
            except KeyError:
                raise FileNotFoundError(f'subkey not found, key="{current_fake_reg_key.full_key}", subkey="{key_part}"')
    return current_fake_reg_key


def set_fake_reg_value(
    fake_reg_key: FakeRegistryKey,
    sub_key: str,
    value_name: str,
    value: None | bytes | str | list[str] | int,
    value_type: int = REG_SZ,
    last_modified_ns: int | None = None,
) -> FakeRegistryValue:
    r"""Set a registry value, creating parent keys on the fly if needed.

    >>> fake_reg_root = FakeRegistryKey()
    >>> fake_reg_key = set_fake_reg_key(
    ...     fake_reg_key=fake_reg_root,
    ...     sub_key=r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT',
    ... )
    >>> fake_reg_value = set_fake_reg_value(fake_reg_key, '', 'CurrentBuild', '18363', REG_SZ)
    >>> assert fake_reg_value.full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT'
    >>> assert fake_reg_value.value_name == 'CurrentBuild'
    >>> assert fake_reg_value.value == '18363'
    >>> assert fake_reg_value.value_type == REG_SZ
    """
    if last_modified_ns is None:
        last_modified_ns = get_windows_timestamp_now()

    fake_reg_key = set_fake_reg_key(fake_reg_key=fake_reg_key, sub_key=sub_key, last_modified_ns=last_modified_ns)

    if value_name not in fake_reg_key.values:
        fake_reg_key.values[value_name] = FakeRegistryValue()
        fake_reg_value = fake_reg_key.values[value_name]
        fake_reg_value.full_key = fake_reg_key.full_key
        fake_reg_value.value_name = value_name
    else:
        fake_reg_value = fake_reg_key.values[value_name]

    fake_reg_value.value = value
    fake_reg_value.value_type = value_type
    fake_reg_value.last_modified_ns = last_modified_ns
    return fake_reg_value


def get_windows_timestamp_now() -> int:
    """Return current time as Windows timestamp (100ns intervals since 1601-01-01).

    >>> assert get_windows_timestamp_now() > 10000
    """
    linux_timestamp_100ns = int(time.time() * 1e7)
    linux_windows_diff_100ns = int(11644473600 * 1e7)
    return linux_timestamp_100ns + linux_windows_diff_100ns


__all__ = [
    "FakeRegistry",
    "FakeRegistryKey",
    "FakeRegistryValue",
    "get_fake_reg_key",
    "get_windows_timestamp_now",
    "set_fake_reg_key",
    "set_fake_reg_value",
]
