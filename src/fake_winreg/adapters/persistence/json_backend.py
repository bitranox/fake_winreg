"""JSON file-backed registry backend.

Loads the entire JSON file into an InMemoryBackend on construction,
then delegates all operations to it. Call :meth:`save` to persist
the current state back to disk.
"""

from __future__ import annotations

from pathlib import Path

import orjson

from fake_winreg.domain.memory_backend import InMemoryBackend
from fake_winreg.domain.registry import FakeRegistry, FakeRegistryKey, FakeRegistryValue
from fake_winreg.domain.serialization import dict_to_registry, registry_to_dict
from fake_winreg.domain.types import RegData


class JsonBackend:
    """Registry backend that persists state as a JSON file.

    On construction the file is read, deserialized, and loaded into an
    :class:`InMemoryBackend`.  All read/write operations are delegated
    to the inner backend.  Call :meth:`save` to write the current state
    back to disk.

    If *path* does not exist, an empty registry is created.

    >>> import tempfile, os
    >>> p = os.path.join(tempfile.mkdtemp(), "test.json")
    >>> backend = JsonBackend(p)
    >>> hive = backend.get_hive(18446744071562067970)
    >>> assert hive.full_key == 'HKEY_LOCAL_MACHINE'
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        registry = self._load_registry()
        self._inner = InMemoryBackend(registry)

    def _load_registry(self) -> FakeRegistry:
        """Read and deserialize the JSON file, or return an empty registry."""
        if not self._path.exists():
            return FakeRegistry()
        raw = self._path.read_bytes()
        if not raw:
            return FakeRegistry()
        data = orjson.loads(raw)
        return dict_to_registry(data)

    # ------------------------------------------------------------------
    # Delegated RegistryBackend methods
    # ------------------------------------------------------------------

    def get_hive(self, hive_key: int) -> FakeRegistryKey:
        """Return the root key for a predefined HKEY_* constant."""
        return self._inner.get_hive(hive_key)

    def get_key(self, base_key: FakeRegistryKey, sub_key: str) -> FakeRegistryKey:
        """Retrieve an existing key. Raises FileNotFoundError if missing."""
        return self._inner.get_key(base_key, sub_key)

    def create_key(self, base_key: FakeRegistryKey, sub_key: str | None) -> FakeRegistryKey:
        """Create a key and intermediate parents."""
        return self._inner.create_key(base_key, sub_key)

    def delete_key(self, base_key: FakeRegistryKey, sub_key: str) -> None:
        """Delete a leaf key. Raises PermissionError if it has subkeys."""
        self._inner.delete_key(base_key, sub_key)

    def get_value(self, key: FakeRegistryKey, value_name: str) -> FakeRegistryValue:
        """Retrieve a value. Raises KeyError if missing."""
        return self._inner.get_value(key, value_name)

    def set_value(self, key: FakeRegistryKey, value_name: str, value: RegData, value_type: int) -> None:
        """Create or update a value."""
        self._inner.set_value(key, value_name, value, value_type)

    def delete_value(self, key: FakeRegistryKey, value_name: str) -> None:
        """Delete a value. Raises KeyError if missing."""
        self._inner.delete_value(key, value_name)

    def enum_keys(self, key: FakeRegistryKey) -> list[str]:
        """List subkey names."""
        return self._inner.enum_keys(key)

    def enum_values(self, key: FakeRegistryKey) -> list[tuple[str, RegData, int]]:
        """List values as (name, data, type) tuples."""
        return self._inner.enum_values(key)

    def query_info(self, key: FakeRegistryKey) -> tuple[int, int, int]:
        """Return (num_subkeys, num_values, last_modified_ns)."""
        return self._inner.query_info(key)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Write current state back to the JSON file.

        >>> import tempfile, os
        >>> p = os.path.join(tempfile.mkdtemp(), "save_test.json")
        >>> backend = JsonBackend(p)
        >>> backend.save()
        >>> assert os.path.exists(p)
        """
        data = registry_to_dict(self._inner.registry)
        raw = orjson.dumps(data, option=orjson.OPT_INDENT_2)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_bytes(raw)


__all__ = ["JsonBackend"]
