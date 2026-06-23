"""In-memory registry backend wrapping FakeRegistry.

This is the default backend — all data lives in Python dicts in memory.
Equivalent to the original fake_winreg behavior before backends were introduced.
"""

from __future__ import annotations

from .registry import (
    FakeRegistry,
    FakeRegistryKey,
    FakeRegistryValue,
    get_fake_reg_key,
    set_fake_reg_key,
    set_fake_reg_value,
)
from .types import RegData


class InMemoryBackend:
    """Registry backend storing everything in memory via FakeRegistry.

    >>> backend = InMemoryBackend()
    >>> key = backend.get_hive(18446744071562067970)
    >>> assert key.full_key == 'HKEY_LOCAL_MACHINE'
    """

    def __init__(self, registry: FakeRegistry | None = None) -> None:
        self._registry = registry if registry is not None else FakeRegistry()

    @property
    def registry(self) -> FakeRegistry:
        """Access the underlying FakeRegistry (for backward compat)."""
        return self._registry

    def get_hive(self, hive_key: int) -> FakeRegistryKey:
        """Return the root key for a predefined HKEY_* constant."""
        try:
            return self._registry.hive[hive_key]
        except KeyError:
            error = OSError("[WinError 6] The handle is invalid")
            error.winerror = 6  # type: ignore[attr-defined]
            raise error

    def get_key(self, base_key: FakeRegistryKey, sub_key: str) -> FakeRegistryKey:
        """Retrieve an existing key. Raises FileNotFoundError if missing."""
        try:
            return get_fake_reg_key(base_key, sub_key)
        except FileNotFoundError:
            error = FileNotFoundError("[WinError 2] The system cannot find the file specified")
            error.winerror = 2  # type: ignore[attr-defined]
            raise error

    def create_key(self, base_key: FakeRegistryKey, sub_key: str | None) -> FakeRegistryKey:
        """Create a key and intermediate parents."""
        return set_fake_reg_key(base_key, sub_key)

    def delete_key(self, base_key: FakeRegistryKey, sub_key: str) -> None:
        """Delete a leaf key. Raises PermissionError if it has subkeys."""
        try:
            target = get_fake_reg_key(base_key, sub_key)
        except FileNotFoundError:
            error = FileNotFoundError("[WinError 2] The system cannot find the file specified")
            error.winerror = 2  # type: ignore[attr-defined]
            raise error

        if target.subkeys:
            permission_error = PermissionError("[WinError 5] Access is denied")
            permission_error.winerror = 5  # type: ignore[attr-defined]
            raise permission_error

        full_key_path = target.full_key
        leaf_name = full_key_path.rsplit("\\", 1)[1]
        parent = target.parent_fake_registry_key
        if parent is None:  # pragma: no cover
            raise RuntimeError("Cannot delete a root registry key")
        parent.subkeys.pop(leaf_name, None)

    def get_value(self, key: FakeRegistryKey, value_name: str) -> FakeRegistryValue:
        """Retrieve a value. Raises KeyError if missing."""
        try:
            return key.values[value_name]
        except KeyError:
            error = FileNotFoundError("[WinError 2] The system cannot find the file specified")
            error.winerror = 2  # type: ignore[attr-defined]
            raise error

    def set_value(self, key: FakeRegistryKey, value_name: str, value: RegData, value_type: int) -> None:
        """Create or update a value."""
        set_fake_reg_value(key, sub_key="", value_name=value_name, value=value, value_type=value_type)

    def delete_value(self, key: FakeRegistryKey, value_name: str) -> None:
        """Delete a value. Raises KeyError if missing."""
        try:
            del key.values[value_name]
        except KeyError:
            error = FileNotFoundError("[WinError 2] The system cannot find the file specified")
            error.winerror = 2  # type: ignore[attr-defined]
            raise error

    def enum_keys(self, key: FakeRegistryKey) -> list[str]:
        """List subkey names in insertion order."""
        return list(key.subkeys.keys())

    def enum_values(self, key: FakeRegistryKey) -> list[tuple[str, RegData, int]]:
        """List values as (name, data, type) tuples in insertion order."""
        return [(v.value_name, v.value, v.value_type) for v in key.values.values()]

    def query_info(self, key: FakeRegistryKey) -> tuple[int, int, int]:
        """Return (num_subkeys, num_values, last_modified_ns)."""
        return len(key.subkeys), len(key.values), key.last_modified_ns


__all__ = ["InMemoryBackend"]
