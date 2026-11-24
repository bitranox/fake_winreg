"""SQLite-backed registry storage.

Reads and writes registry keys and values directly to a SQLite database
instead of holding the full tree in memory.  Implements the same interface
as ``InMemoryBackend``.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, cast

import orjson

from fake_winreg.domain.constants import hive_name_hashed_by_int
from fake_winreg.domain.registry import (
    FakeRegistryKey,
    FakeRegistryValue,
    get_windows_timestamp_now,
)
from fake_winreg.domain.serialization import decode_value, encode_value
from fake_winreg.domain.types import KeyInfo, ValueEntry

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from types import TracebackType

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

# Every child lookup (enum_keys, the subkey count, delete_key's has-children
# check) filters on parent_path; without this index each one scans the whole
# table, which made a full tree walk quadratic in the number of keys. IF NOT
# EXISTS so databases created before the index get it on their next open.
_CREATE_PARENT_INDEX = "CREATE INDEX IF NOT EXISTS ix_registry_keys_parent_path ON registry_keys(parent_path)"


def _encode_value(value: RegData) -> str | None:
    """Encode a registry value for SQLite TEXT storage.

    The column holds the same JSON the JSON snapshot format uses for a value
    (bytes as a ``{"_base64": ...}`` marker), so both formats share one encoder.
    None is stored as SQL NULL rather than the JSON text ``null``.

    >>> _encode_value("hello")
    '"hello"'
    >>> _encode_value(b"\\x00")
    '{"_base64":"AA=="}'
    >>> _encode_value(None) is None
    True
    """
    if value is None:
        return None
    # orjson would also store a float or a dict; refuse what is not registry data.
    if not isinstance(value, (bytes, str, int, list)):  # pyright: ignore[reportUnnecessaryIsInstance]
        msg = f"Unsupported value type: {type(value)}"
        raise TypeError(msg)
    return orjson.dumps(encode_value(value)).decode()


def _decode_value(raw: str | None) -> RegData:
    """Decode a registry value from SQLite TEXT storage.

    >>> _decode_value(None) is None
    True
    >>> _decode_value('"hello"'), _decode_value('42'), _decode_value('{"_base64":"AA=="}')
    ('hello', 42, b'\\x00')
    """
    if raw is None:
        return None
    return decode_value(orjson.loads(raw))


def _hive_name_from_path(full_path: str) -> str:
    """Extract the hive root name from a full key path."""
    return full_path.split("\\", 1)[0]


def _make_key(full_path: str) -> FakeRegistryKey:
    """Build a lightweight FakeRegistryKey with only ``full_key`` set."""
    key = FakeRegistryKey()
    key.full_key = full_path
    return key


def _not_found_error() -> FileNotFoundError:
    """Build the error real winreg raises for a missing key or value."""
    error = FileNotFoundError("[WinError 2] The system cannot find the file specified")
    error.winerror = 2  # type: ignore[attr-defined]
    return error


def _invalid_handle_error() -> OSError:
    """Build the error real winreg raises for an unknown root handle."""
    error = OSError("[WinError 6] The handle is invalid")
    error.winerror = 6  # type: ignore[attr-defined]
    return error


def _list_position(index: int, count: Callable[[], int]) -> int:
    """Turn a list-style index into a non-negative OFFSET, as ``list[index]`` would read it.

    A negative index counts from the end, so EnumKey(key, -1) keeps returning
    the last entry as it does on every other backend. It must be resolved here:
    SQLite reads a negative OFFSET as 0 and would silently return the first row.
    The count is only queried for a negative index.

    >>> _list_position(2, lambda: 5), _list_position(-1, lambda: 5)
    (2, 4)
    """
    if index >= 0:
        return index
    position = count() + index
    if position < 0:
        raise IndexError(index)
    return position


class SqliteBackend:
    """Registry backend storing keys and values in a SQLite database.

    Each write commits on its own, unless it runs inside :meth:`bulk`.

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
        self._bulk_depth = 0
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

    # -- transactions --------------------------------------------------------

    @contextmanager
    def bulk(self) -> Generator[None, None, None]:
        """Group every write inside the block into one transaction.

        A commit costs a disk sync (about 1 ms each, measured), so a bulk load
        that commits per key spends most of its time syncing. Inside the block
        writes are committed once at the end, or rolled back if the block
        raises. Blocks nest: an inner block is a SAVEPOINT, so an exception the
        outer block catches undoes only the inner block's writes.

        Example:
            >>> import tempfile, os
            >>> db_path = os.path.join(tempfile.mkdtemp(), "bulk.db")
            >>> with SqliteBackend(db_path) as backend:
            ...     hive = backend.get_hive(18446744071562067970)
            ...     with backend.bulk():
            ...         _ = backend.create_key(hive, "SOFTWARE\\\\Bulk")
            ...     backend.enum_keys(hive)
            ['SOFTWARE']
        """
        depth = self._bulk_depth
        savepoint = f"bulk_{depth}"
        if depth == 0:
            # An explicit BEGIN, because a SAVEPOINT that opens the transaction
            # itself would commit it on RELEASE, out of the outer block's reach.
            if not self._conn.in_transaction:
                self._conn.execute("BEGIN")
        else:
            self._conn.execute(f"SAVEPOINT {savepoint}")
        self._bulk_depth = depth + 1
        try:
            yield
        except BaseException:
            self._bulk_depth = depth
            self._end_block(depth, savepoint, success=False)
            raise
        self._bulk_depth = depth
        self._end_block(depth, savepoint, success=True)

    def _end_block(self, depth: int, savepoint: str, *, success: bool) -> None:
        """Commit or roll back the outermost block, release or undo an inner one."""
        if depth == 0:
            if success:
                self._conn.commit()
            else:
                self._conn.rollback()
            return
        if not success:
            self._conn.execute(f"ROLLBACK TO {savepoint}")
        self._conn.execute(f"RELEASE {savepoint}")

    def _commit(self) -> None:
        """Commit a single write, unless a :meth:`bulk` block commits it later."""
        if self._bulk_depth == 0:
            self._conn.commit()

    # -- schema setup --------------------------------------------------------

    def _initialize_schema(self) -> None:
        """Create tables and indexes if they do not exist."""
        self._conn.execute(_CREATE_KEYS_TABLE)
        self._conn.execute(_CREATE_VALUES_TABLE)
        self._conn.execute(_CREATE_PARENT_INDEX)
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
            raise _invalid_handle_error() from None

        row = self._conn.execute(
            "SELECT full_path FROM registry_keys WHERE full_path = ?",
            (hive_name,),
        ).fetchone()
        if row is None:  # pragma: no cover - hives are always seeded
            raise _invalid_handle_error()
        return _make_key(row[0])

    def get_key(self, base_key: FakeRegistryKey, sub_key: str) -> FakeRegistryKey:
        """Retrieve an existing key. Raises FileNotFoundError if missing."""
        full_path = _build_full_path(base_key.full_key, sub_key)
        row = self._conn.execute(
            "SELECT full_path FROM registry_keys WHERE full_path = ?",
            (full_path,),
        ).fetchone()
        if row is None:
            raise _not_found_error()
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
        self._commit()
        return _make_key(current)

    def delete_key(self, base_key: FakeRegistryKey, sub_key: str) -> None:
        """Delete a leaf key. Raises PermissionError if it has subkeys."""
        full_path = _build_full_path(base_key.full_key, sub_key)

        row = self._conn.execute(
            "SELECT full_path FROM registry_keys WHERE full_path = ?",
            (full_path,),
        ).fetchone()
        if row is None:
            raise _not_found_error()

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
        self._commit()

    def get_value(self, key: FakeRegistryKey, value_name: str) -> FakeRegistryValue:
        """Retrieve a value. Raises FileNotFoundError if missing."""
        row = self._conn.execute(
            "SELECT value_name, data, value_type, last_modified_ns FROM registry_values "
            "WHERE full_path = ? AND value_name = ?",
            (key.full_key, value_name),
        ).fetchone()
        if row is None:
            raise _not_found_error()

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
        self._commit()

    def delete_value(self, key: FakeRegistryKey, value_name: str) -> None:
        """Delete a value. Raises FileNotFoundError if missing."""
        cursor = self._conn.execute(
            "DELETE FROM registry_values WHERE full_path = ? AND value_name = ?",
            (key.full_key, value_name),
        )
        self._commit()
        if cursor.rowcount == 0:
            raise _not_found_error()

    def enum_keys(self, key: FakeRegistryKey) -> list[str]:
        """List subkey names."""
        rows = self._conn.execute(
            "SELECT full_path FROM registry_keys WHERE parent_path = ? ORDER BY full_path",
            (key.full_key,),
        ).fetchall()
        return [row[0].rsplit("\\", 1)[-1] for row in rows]

    def subkey_name_at(self, key: FakeRegistryKey, index: int) -> str:
        """Return the name of the subkey at *index*, in :meth:`enum_keys` order.

        Reads one row, so ``EnumKey`` over N subkeys does not fetch all N per call.
        A negative *index* counts from the end, as list indexing does.

        Raises:
            IndexError: If *index* is out of range either way.
        """
        position = _list_position(index, lambda: self._count_subkeys(key))
        row = self._conn.execute(
            "SELECT full_path FROM registry_keys WHERE parent_path = ? ORDER BY full_path LIMIT 1 OFFSET ?",
            (key.full_key, position),
        ).fetchone()
        if row is None:
            raise IndexError(index)
        return cast("str", row[0]).rsplit("\\", 1)[-1]

    def enum_values(self, key: FakeRegistryKey) -> list[ValueEntry]:
        """List the key's values, ordered by name."""
        rows = self._conn.execute(
            "SELECT value_name, data, value_type FROM registry_values WHERE full_path = ? ORDER BY value_name",
            (key.full_key,),
        ).fetchall()
        return [ValueEntry(name=row[0], data=_decode_value(row[1]), value_type=row[2]) for row in rows]

    def value_at(self, key: FakeRegistryKey, index: int) -> ValueEntry:
        """Return the value at *index*, in :meth:`enum_values` order.

        A negative *index* counts from the end, as list indexing does.

        Raises:
            IndexError: If *index* is out of range either way.
        """
        position = _list_position(index, lambda: self._count_values(key))
        row = self._conn.execute(
            "SELECT value_name, data, value_type FROM registry_values WHERE full_path = ? "
            "ORDER BY value_name LIMIT 1 OFFSET ?",
            (key.full_key, position),
        ).fetchone()
        if row is None:
            raise IndexError(index)
        return ValueEntry(name=row[0], data=_decode_value(row[1]), value_type=row[2])

    def query_info(self, key: FakeRegistryKey) -> KeyInfo:
        """Return the key's subkey count, value count and last-modified time."""
        row = self._conn.execute(
            "SELECT last_modified_ns FROM registry_keys WHERE full_path = ?",
            (key.full_key,),
        ).fetchone()
        last_modified_ns = row[0] if row else 0

        return KeyInfo(
            subkey_count=self._count_subkeys(key),
            value_count=self._count_values(key),
            last_modified_ns=last_modified_ns,
        )

    def _count_subkeys(self, key: FakeRegistryKey) -> int:
        """Count the direct subkeys of *key*."""
        return cast(
            "int",
            self._conn.execute("SELECT COUNT(*) FROM registry_keys WHERE parent_path = ?", (key.full_key,)).fetchone()[
                0
            ],
        )

    def _count_values(self, key: FakeRegistryKey) -> int:
        """Count the values of *key*."""
        return cast(
            "int",
            self._conn.execute("SELECT COUNT(*) FROM registry_values WHERE full_path = ?", (key.full_key,)).fetchone()[
                0
            ],
        )


def _build_full_path(base_full_key: str, sub_key: str) -> str:
    """Combine base key path and sub_key into a full path."""
    if sub_key:
        return base_full_key + "\\" + sub_key
    return base_full_key


__all__ = ["SqliteBackend"]
