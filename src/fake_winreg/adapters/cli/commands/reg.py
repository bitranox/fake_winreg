"""CLI commands for persistent registry operations.

Provides a ``reg`` command group with subcommands to query and modify
a SQLite-backed registry database.
"""

from __future__ import annotations

import binascii
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import rich_click as click

from fake_winreg.domain.constants import (
    REG_BINARY,
    REG_DWORD,
    REG_EXPAND_SZ,
    REG_MULTI_SZ,
    REG_NONE,
    REG_QWORD,
    REG_SZ,
    hive_int_by_name,
)

from .. import safe_console
from ..config_load import require_config
from ..constants import click_context_settings
from ..context import CLIContext
from ..typed_click import argument, option

if TYPE_CHECKING:
    from collections.abc import Generator, Mapping

    from fake_winreg.adapters.persistence.sqlite_backend import SqliteBackend
    from fake_winreg.domain.registry import FakeRegistryKey

logger = logging.getLogger(__name__)

#: The value types ``reg set --type`` accepts, by the name the command line uses for them.
_TYPE_BY_NAME: Final[Mapping[str, int]] = MappingProxyType(
    {
        "REG_SZ": REG_SZ,
        "REG_EXPAND_SZ": REG_EXPAND_SZ,
        "REG_BINARY": REG_BINARY,
        "REG_DWORD": REG_DWORD,
        "REG_QWORD": REG_QWORD,
        "REG_MULTI_SZ": REG_MULTI_SZ,
        "REG_NONE": REG_NONE,
    }
)

#: The same table the other way round, for ``list-values``.
_NAME_BY_TYPE: Final[Mapping[int, str]] = MappingProxyType({value: name for name, value in _TYPE_BY_NAME.items()})

_NO_DB_MESSAGE = (
    "No registry database specified. Use --db PATH or configure registry.db_path "
    "in config (--set registry.db_path=PATH or REGISTRY__DB_PATH in .env)."
)


@dataclass(frozen=True, slots=True)
class _RegGroupState:
    """What the ``reg`` group's own options leave for its subcommands.

    Attributes:
        db_path: The ``--db`` path, or None when it was not given (or given empty), so the
            configuration decides.
    """

    db_path: Path | None


@dataclass(frozen=True, slots=True)
class _KeyPath:
    """A full key path from the command line, split and with its hive resolved.

    Attributes:
        text: The path as typed, for messages.
        hive: The ``HKEY_*`` value of its first component.
        sub_path: Everything after the hive, empty for the hive itself.
    """

    text: str
    hive: int
    sub_path: str


@dataclass(frozen=True, slots=True)
class _OpenedKey:
    """An open database and one key in it, valid for the length of a ``with`` block."""

    backend: SqliteBackend
    key: FakeRegistryKey


def _resolve_db_path(ctx: click.Context, db_option: Path | None) -> Path:
    """Resolve the database path from --db option or config.

    Only without ``--db`` is the configuration read, so only then does a configuration that
    could not be loaded refuse the command (exit 78, naming why).
    """
    if db_option is not None:
        return db_option

    # The reg group keeps its own state in ctx.obj, which hides the root's CLIContext from
    # get_cli_context; find_object looks up the context chain for it instead. None means the
    # group runs without the root group, so there is no configuration to read.
    cli_ctx = ctx.find_object(CLIContext)
    if cli_ctx is None:
        raise click.UsageError(_NO_DB_MESSAGE)
    configured = require_config(ctx, cli_ctx).get("registry.db_path", default=None)
    if not configured:
        raise click.UsageError(_NO_DB_MESSAGE)
    return Path(str(configured))


def _parse_key_path(key_path: str) -> _KeyPath:
    """Split a full key path at its first backslash and resolve the hive.

    Raises:
        click.UsageError: The first component names no hive.

    >>> parsed = _parse_key_path(r"HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft")
    >>> parsed.sub_path
    'SOFTWARE\\\\Microsoft'
    >>> parsed.hive == hive_int_by_name["HKEY_LOCAL_MACHINE"]
    True
    >>> _parse_key_path("HKEY_USERS").sub_path
    ''
    """
    hive_name, _, sub_path = key_path.partition("\\")
    hive = hive_int_by_name.get(hive_name)
    if hive is None:
        raise click.UsageError(f"Unknown hive: {hive_name}")
    return _KeyPath(text=key_path, hive=hive, sub_path=sub_path)


@contextmanager
def _open_backend(db_path: Path) -> Generator[SqliteBackend]:
    """Open the SQLite registry at ``db_path`` for a ``with`` block and close it afterwards."""
    # Deferred: sqlite_backend pulls in orjson/sqlite3 - keep it out of `--help` and
    # every other subcommand's path; only db-backed reg subcommands need it.
    from fake_winreg.adapters.persistence.sqlite_backend import SqliteBackend  # noqa: PLC0415

    with SqliteBackend(db_path) as backend:
        yield backend


@contextmanager
def _open_key(db_path: Path, key_path: _KeyPath) -> Generator[_OpenedKey]:
    """Open the database and resolve ``key_path`` in it, closing the database afterwards.

    Raises:
        click.UsageError: The key does not exist.
    """
    with _open_backend(db_path) as backend:
        hive_key = backend.get_hive(key_path.hive)
        if not key_path.sub_path:
            yield _OpenedKey(backend=backend, key=hive_key)
            return
        try:
            reg_key = backend.get_key(hive_key, key_path.sub_path)
        except FileNotFoundError as exc:
            raise click.UsageError(f"Key not found: {key_path.text}") from exc
        yield _OpenedKey(backend=backend, key=reg_key)


def _parse_reg_type(_ctx: click.Context, _param: click.Parameter, value: str) -> int:
    """The ``--type`` callback: a type name, in any case, as its ``REG_*`` number.

    A callback rather than a ``click.Choice``: the refusal keeps the message this command has
    always given for an unknown type, which a Choice would replace with its own.

    Raises:
        click.UsageError: The name is not one of the types in the table.
    """
    type_int = _TYPE_BY_NAME.get(value.upper())
    if type_int is None:
        valid = ", ".join(sorted(_TYPE_BY_NAME))
        raise click.UsageError(f"Unknown type: {value}. Valid types: {valid}")
    return type_int


def _format_value_data(data: bytes | int | str | list[str] | None, value_type: int) -> str:
    """Format a registry value for display."""
    if data is None:
        return "(none)"
    if isinstance(data, bytes):
        return data.hex()
    if isinstance(data, list):
        return ", ".join(data)
    return str(data)


# ---------------------------------------------------------------------------
# Command group
# ---------------------------------------------------------------------------


@click.group("reg", context_settings=click_context_settings())
@option("--db", "db_path", default=None, type=click.Path(), help="Path to SQLite registry database.")
@click.pass_context
def cli_reg(ctx: click.Context, db_path: str | None) -> None:
    """Query and modify a persistent SQLite registry.

    \b
    The database path is resolved in order:
      1. --db PATH (this option)
      2. registry.db_path from config (--set, .env, TOML config)

    \b
    Examples:
      fake-winreg reg --db my.db list-keys HKEY_LOCAL_MACHINE
      fake-winreg --set registry.db_path=my.db reg list-keys HKEY_LOCAL_MACHINE
    """
    # An empty --db counts as not given, so the configuration decides; Path("") would be ".".
    ctx.obj = _RegGroupState(db_path=Path(db_path) if db_path else None)


def _get_db_path(ctx: click.Context) -> Path:
    """Get the DB path from the reg group's --db option or config."""
    state = ctx.find_object(_RegGroupState)
    return _resolve_db_path(ctx, state.db_path if state is not None else None)


# ---------------------------------------------------------------------------
# Key commands
# ---------------------------------------------------------------------------


@cli_reg.command("list-keys", context_settings=click_context_settings())
@argument("key_path")
@click.pass_context
def cli_reg_list_keys(ctx: click.Context, key_path: str) -> None:
    """List subkeys of a registry key.

    \b
    Example:
      fake-winreg reg --db my.db list-keys HKEY_LOCAL_MACHINE\\SOFTWARE
    """
    db_path = _get_db_path(ctx)
    with _open_key(db_path, _parse_key_path(key_path)) as opened:
        for name in opened.backend.enum_keys(opened.key):
            safe_console.echo(name)


@cli_reg.command("create-key", context_settings=click_context_settings())
@argument("key_path")
@click.pass_context
def cli_reg_create_key(ctx: click.Context, key_path: str) -> None:
    """Create a registry key (and intermediate parents).

    \b
    Example:
      fake-winreg reg --db my.db create-key HKEY_LOCAL_MACHINE\\SOFTWARE\\MyApp
    """
    db_path = _get_db_path(ctx)
    parsed = _parse_key_path(key_path)
    if not parsed.sub_path:
        raise click.UsageError("Cannot create a root hive key.")

    with _open_backend(db_path) as backend:
        backend.create_key(backend.get_hive(parsed.hive), parsed.sub_path)


@cli_reg.command("delete-key", context_settings=click_context_settings())
@argument("key_path")
@click.pass_context
def cli_reg_delete_key(ctx: click.Context, key_path: str) -> None:
    """Delete a registry key (must have no subkeys).

    \b
    Example:
      fake-winreg reg --db my.db delete-key HKEY_LOCAL_MACHINE\\SOFTWARE\\MyApp
    """
    db_path = _get_db_path(ctx)
    parsed = _parse_key_path(key_path)
    if not parsed.sub_path:
        raise click.UsageError("Cannot delete a root hive key.")

    with _open_backend(db_path) as backend:
        try:
            backend.delete_key(backend.get_hive(parsed.hive), parsed.sub_path)
        except FileNotFoundError as exc:
            raise click.UsageError(f"Key not found: {key_path}") from exc
        except PermissionError as exc:
            raise click.UsageError(f"Cannot delete key with subkeys: {key_path}") from exc


@cli_reg.command("info", context_settings=click_context_settings())
@argument("key_path")
@click.pass_context
def cli_reg_info(ctx: click.Context, key_path: str) -> None:
    """Show key information (subkey count, value count, last modified).

    \b
    Example:
      fake-winreg reg --db my.db info HKEY_LOCAL_MACHINE\\SOFTWARE
    """
    db_path = _get_db_path(ctx)
    with _open_key(db_path, _parse_key_path(key_path)) as opened:
        info = opened.backend.query_info(opened.key)
    safe_console.echo(f"Subkeys: {info.subkey_count}")
    safe_console.echo(f"Values:  {info.value_count}")
    safe_console.echo(f"Last modified: {info.last_modified_ns}")


# ---------------------------------------------------------------------------
# Value commands
# ---------------------------------------------------------------------------


@cli_reg.command("list-values", context_settings=click_context_settings())
@argument("key_path")
@click.pass_context
def cli_reg_list_values(ctx: click.Context, key_path: str) -> None:
    """List all values in a registry key.

    \b
    Example:
      fake-winreg reg --db my.db list-values HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion
    """
    db_path = _get_db_path(ctx)
    with _open_key(db_path, _parse_key_path(key_path)) as opened:
        values = opened.backend.enum_values(opened.key)
    if not values:
        return
    name_width = max(len(entry.name) or 9 for entry in values)  # 9 = len("(Default)")
    for entry in values:
        display_name = entry.name or "(Default)"
        type_name = _NAME_BY_TYPE.get(entry.value_type, f"REG_({entry.value_type})")
        display_data = _format_value_data(entry.data, entry.value_type)
        safe_console.echo(f"{display_name:<{name_width}}  {type_name:<14}  {display_data}")


@cli_reg.command("get", context_settings=click_context_settings())
@argument("key_path")
@argument("value_name")
@click.pass_context
def cli_reg_get(ctx: click.Context, key_path: str, value_name: str) -> None:
    """Get a specific registry value.

    \b
    Example:
      fake-winreg reg --db my.db get HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion CurrentBuild
    """
    db_path = _get_db_path(ctx)
    with _open_key(db_path, _parse_key_path(key_path)) as opened:
        try:
            fval = opened.backend.get_value(opened.key, value_name)
        except (KeyError, FileNotFoundError) as exc:
            raise click.UsageError(f"Value not found: {value_name}") from exc
    safe_console.echo(_format_value_data(fval.value, fval.value_type))


@cli_reg.command("set", context_settings=click_context_settings())
@argument("key_path")
@argument("value_name")
@argument("data")
@option(
    "--type",
    "reg_type",
    default="REG_SZ",
    callback=_parse_reg_type,
    help="Registry type (REG_SZ, REG_DWORD, REG_BINARY, etc.)",
)
@click.pass_context
def cli_reg_set(ctx: click.Context, key_path: str, value_name: str, data: str, reg_type: int) -> None:
    """Set a registry value.

    \b
    Examples:
      fake-winreg reg --db my.db set HKEY_LOCAL_MACHINE\\SOFTWARE\\MyApp Name "hello"
      fake-winreg reg --db my.db set HKEY_LOCAL_MACHINE\\SOFTWARE\\MyApp Count 42 --type REG_DWORD
      fake-winreg reg --db my.db set HKEY_LOCAL_MACHINE\\SOFTWARE\\MyApp Data deadbeef --type REG_BINARY
      fake-winreg reg --db my.db set HKEY_LOCAL_MACHINE\\SOFTWARE\\MyApp List "a,b,c" --type REG_MULTI_SZ
    """
    parsed_data = _parse_value_data(data, reg_type)

    db_path = _get_db_path(ctx)
    parsed = _parse_key_path(key_path)

    with _open_backend(db_path) as backend:
        hive_key = backend.get_hive(parsed.hive)
        reg_key = backend.create_key(hive_key, parsed.sub_path) if parsed.sub_path else hive_key
        backend.set_value(reg_key, value_name, parsed_data, reg_type)


@cli_reg.command("delete-value", context_settings=click_context_settings())
@argument("key_path")
@argument("value_name")
@click.pass_context
def cli_reg_delete_value(ctx: click.Context, key_path: str, value_name: str) -> None:
    """Delete a registry value.

    \b
    Example:
      fake-winreg reg --db my.db delete-value HKEY_LOCAL_MACHINE\\SOFTWARE\\MyApp MyValue
    """
    db_path = _get_db_path(ctx)
    with _open_key(db_path, _parse_key_path(key_path)) as opened:
        try:
            opened.backend.delete_value(opened.key, value_name)
        except (KeyError, FileNotFoundError) as exc:
            raise click.UsageError(f"Value not found: {value_name}") from exc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_value_data(data: str, reg_type: int) -> bytes | int | str | list[str] | None:
    """Parse string input into the appropriate Python type for the registry."""
    if reg_type in (REG_SZ, REG_EXPAND_SZ):
        return data
    if reg_type in (REG_DWORD, REG_QWORD):
        try:
            return int(data)
        except ValueError:
            raise click.UsageError(f"Invalid integer value: {data}")
    if reg_type == REG_BINARY:
        try:
            return binascii.unhexlify(data)
        except (ValueError, binascii.Error):
            raise click.UsageError(f"Invalid hex string: {data}")
    if reg_type == REG_MULTI_SZ:
        return data.split(",")
    if reg_type == REG_NONE:
        return None
    return data


__all__ = ["cli_reg"]
