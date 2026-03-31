"""SQLite-backed registry storage.

Reads and writes registry keys and values directly to a SQLite database
instead of holding the full tree in memory.  Implements the same interface
as ``InMemoryBackend``.
"""

from __future__ import annotations

import base64
import sqlite3
from pathlib import Path
from types import TracebackType
from typing import Any, cast

import orjson

from fake_winreg.domain.constants import hive_name_hashed_by_int
from fake_winreg.domain.registry import (
    FakeRegistryKey,
    FakeRegistryValue,
    get_windows_timestamp_now,
)
from fake_winreg.domain.types import RegData

_CREATE_KEYS_TABLE = """\
CREATE TABLE IF NOT EXISTS registry_keys (
    full_path TEXT PRIMARY KEY,
    hive_name TEXT NOT NULL,
    parent_path TEXT,
    last_modified_ns INTEGER NOT NULL DEFAULT 0
)"""

_CREATE_VALUES_TABLE = """\
CREATE TABLE IF NOT EXISTS registry_values (
    full_path TEXT NOT NULL,
    value_name TEXT NOT NULL,
    data TEXT,
    value_type INTEGER NOT NULL DEFAULT 1,
    last_modified_ns INTEGER,
    PRIMARY KEY (full_path, value_name),
    FOREIGN KEY (full_path) REFERENCES registry_keys(full_path)
)"""


def _encode_value(value: RegData) -> str | None:
    """Encode a registry value for SQLite TEXT storage.

    >>> _encode_value("hello")
    '"hello"'
    >>> _encode_value(42)
    '42'
    >>> _encode_value(None) is None
    True
    """
    if value is None:
        return None
    if isinstance(value, bytes):
        return orjson.dumps({"_base64": base64.b64encode(value).decode()}).decode()
    if isinstance(value, str):
        return orjson.dumps(value).decode()
    if isinstance(value, int):
        return orjson.dumps(value).decode()
    if isinstance(value, list):  # pyright: ignore[reportUnnecessaryIsInstance]
        return orjson.dumps(value).decode()
    msg = f"Unsupported value type: {type(value)}"
    raise TypeError(msg)


def _decode_value(raw: str | None) -> RegData:
    """Decode a registry value from SQLite TEXT storage.

    >>> _decode_value(None) is None
    True
    >>> _decode_value('"hello"')
    'hello'
    >>> _decode_value('42')
    42
    """
    if raw is None:
        return None
    parsed: Any = orjson.loads(raw)
    if isinstance(parsed, dict) and "_base64" in parsed:
        return base64.b64decode(cast(str, parsed["_base64"]))
    return cast(RegData, parsed)


def _hive_name_from_path(full_path: str) -> str:
    """Extract the hive root name from a full key path."""
    return full_path.split("\\", 1)[0]


def _parent_path_from_full(full_path: str) -> str | None:  # pyright: ignore[reportUnusedFunction]
    """Return the parent path, or None for root hive keys."""
    if "\\" not in full_path:
        return None
    return full_path.rsplit("\\", 1)[0]


def _make_key(full_path: str) -> FakeRegistryKey:
    """Build a lightweight FakeRegistryKey with only ``full_key`` set."""
    key = FakeRegistryKey()
    key.full_key = full_path
    return key


class SqliteBackend:
    """Registry backend storing keys and values in a SQLite database.

    >>> import tempfile, os
    >>> db_path = os.path.join(tempfile.mkdtemp(), "test.db")
    >>> with SqliteBackend(db_path) as backend:
    ...     hive = backend.get_hive(18446744071562067970)
    ...     assert hive.full_key == "HKEY_LOCAL_MACHINE"
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._conn = sqlite3.connect(str(self._path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._initialize_schema()
        self._initialize_hives()

    # -- context manager -----------------------------------------------------

    def __enter__(self) -> SqliteBackend:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying database connection."""
        self._conn.close()

    # -- schema setup --------------------------------------------------------

    def _initialize_schema(self) -> None:
        """Create tables if they do not exist."""
        self._conn.execute(_CREATE_KEYS_TABLE)
        self._conn.execute(_CREATE_VALUES_TABLE)
        self._conn.commit()

    def _initialize_hives(self) -> None:
        """Insert predefined hive root keys if absent."""
        now = get_windows_timestamp_now()
        for hive_name in hive_name_hashed_by_int.values():
            self._conn.execute(
                "INSERT OR IGNORE INTO registry_keys (full_path, hive_name, parent_path, last_modified_ns) "
                "VALUES (?, ?, NULL, ?)",
                (hive_name, hive_name, now),
            )
        self._conn.commit()

    # -- RegistryBackend interface -------------------------------------------

    def get_hive(self, hive_key: int) -> FakeRegistryKey:
        """Return the root key for a predefined HKEY_* constant."""
        try:
            hive_name = hive_name_hashed_by_int[hive_key]
        except KeyError:
            error = OSError("[WinError 6] The handle is invalid")
            error.winerror = 6  # type: ignore[attr-defined]
            raise error

        row = self._conn.execute(
            "SELECT full_path FROM registry_keys WHERE full_path = ?",
            (hive_name,),
        ).fetchone()
        if row is None:  # pragma: no cover — hives are always seeded
            error = OSError("[WinError 6] The handle is invalid")
            error.winerror = 6  # type: ignore[attr-defined]
            raise error
        return _make_key(row[0])

    def get_key(self, base_key: FakeRegistryKey, sub_key: str) -> FakeRegistryKey:
        """Retrieve an existing key. Raises FileNotFoundError if missing."""
        full_path = _build_full_path(base_key.full_key, sub_key)
        row = self._conn.execute(
            "SELECT full_path FROM registry_keys WHERE full_path = ?",
            (full_path,),
        ).fetchone()
        if row is None:
            error = FileNotFoundError("[WinError 2] The system cannot find the file specified")
            error.winerror = 2  # type: ignore[attr-defined]
            raise error
        return _make_key(row[0])

    def create_key(self, base_key: FakeRegistryKey, sub_key: str | None) -> FakeRegistryKey:
        """Create a key and all intermediate parents. Returns the leaf key."""
        if not sub_key:
            return _make_key(base_key.full_key)

        now = get_windows_timestamp_now()
        parts = sub_key.split("\\")
        current = base_key.full_key

        for part in parts:
            parent = current
            current = current + "\\" + part if current else part
            hive_name = _hive_name_from_path(current)
            self._conn.execute(
                "INSERT OR IGNORE INTO registry_keys (full_path, hive_name, parent_path, last_modified_ns) "
                "VALUES (?, ?, ?, ?)",
                (current, hive_name, parent, now),
            )
        self._conn.commit()
        return _make_key(current)

    def delete_key(self, base_key: FakeRegistryKey, sub_key: str) -> None:
        """Delete a leaf key. Raises PermissionError if it has subkeys."""
        full_path = _build_full_path(base_key.full_key, sub_key)

        # Verify the key exists
        row = self._conn.execute(
            "SELECT full_path FROM registry_keys WHERE full_path = ?",
            (full_path,),
        ).fetchone()
        if row is None:
            error = FileNotFoundError("[WinError 2] The system cannot find the file specified")
            error.winerror = 2  # type: ignore[attr-defined]
            raise error

        # Check for children
        child = self._conn.execute(
            "SELECT full_path FROM registry_keys WHERE parent_path = ? LIMIT 1",
            (full_path,),
        ).fetchone()
        if child is not None:
            permission_error = PermissionError("[WinError 5] Access is denied")
            permission_error.winerror = 5  # type: ignore[attr-defined]
            raise permission_error

        self._conn.execute("DELETE FROM registry_values WHERE full_path = ?", (full_path,))
        self._conn.execute("DELETE FROM registry_keys WHERE full_path = ?", (full_path,))
        self._conn.commit()

    def get_value(self, key: FakeRegistryKey, value_name: str) -> FakeRegistryValue:
        """Retrieve a value. Raises FileNotFoundError if missing."""
        row = self._conn.execute(
            "SELECT value_name, data, value_type, last_modified_ns FROM registry_values "
            "WHERE full_path = ? AND value_name = ?",
            (key.full_key, value_name),
        ).fetchone()
        if row is None:
            error = FileNotFoundError("[WinError 2] The system cannot find the file specified")
            error.winerror = 2  # type: ignore[attr-defined]
            raise error

        val = FakeRegistryValue()
        val.full_key = key.full_key
        val.value_name = row[0]
        val.value = _decode_value(row[1])
        val.value_type = row[2]
        val.last_modified_ns = row[3]
        return val

    def set_value(self, key: FakeRegistryKey, value_name: str, value: RegData, value_type: int) -> None:
        """Create or update a value."""
        now = get_windows_timestamp_now()
        encoded = _encode_value(value)
        self._conn.execute(
            "INSERT OR REPLACE INTO registry_values (full_path, value_name, data, value_type, last_modified_ns) "
            "VALUES (?, ?, ?, ?, ?)",
            (key.full_key, value_name, encoded, value_type, now),
        )
        self._conn.commit()

    def delete_value(self, key: FakeRegistryKey, value_name: str) -> None:
        """Delete a value. Raises FileNotFoundError if missing."""
        cursor = self._conn.execute(
            "DELETE FROM registry_values WHERE full_path = ? AND value_name = ?",
            (key.full_key, value_name),
        )
        self._conn.commit()
        if cursor.rowcount == 0:
            error = FileNotFoundError("[WinError 2] The system cannot find the file specified")
            error.winerror = 2  # type: ignore[attr-defined]
            raise error

    def enum_keys(self, key: FakeRegistryKey) -> list[str]:
        """List subkey names."""
        rows = self._conn.execute(
            "SELECT full_path FROM registry_keys WHERE parent_path = ? ORDER BY full_path",
            (key.full_key,),
        ).fetchall()
        return [row[0].rsplit("\\", 1)[-1] for row in rows]

    def enum_values(self, key: FakeRegistryKey) -> list[tuple[str, RegData, int]]:
        """List values as (name, data, type) tuples."""
        rows = self._conn.execute(
            "SELECT value_name, data, value_type FROM registry_values WHERE full_path = ? ORDER BY value_name",
            (key.full_key,),
        ).fetchall()
        return [(row[0], _decode_value(row[1]), row[2]) for row in rows]

    def query_info(self, key: FakeRegistryKey) -> tuple[int, int, int]:
        """Return (num_subkeys, num_values, last_modified_ns)."""
        num_subkeys = self._conn.execute(
            "SELECT COUNT(*) FROM registry_keys WHERE parent_path = ?",
            (key.full_key,),
        ).fetchone()[0]

        num_values = self._conn.execute(
            "SELECT COUNT(*) FROM registry_values WHERE full_path = ?",
            (key.full_key,),
        ).fetchone()[0]

        row = self._conn.execute(
            "SELECT last_modified_ns FROM registry_keys WHERE full_path = ?",
            (key.full_key,),
        ).fetchone()
        last_modified_ns = row[0] if row else 0

        return num_subkeys, num_values, last_modified_ns


def _build_full_path(base_full_key: str, sub_key: str) -> str:
    """Combine base key path and sub_key into a full path."""
    if sub_key:
        return base_full_key + "\\" + sub_key
    return base_full_key


__all__ = ["SqliteBackend"]
