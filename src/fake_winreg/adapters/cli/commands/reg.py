"""CLI commands for persistent registry operations.

Provides a ``reg`` command group with subcommands to query and modify
a SQLite-backed registry database.
"""

from __future__ import annotations

import binascii
import logging
from pathlib import Path

import rich_click as click

from ..constants import CLICK_CONTEXT_SETTINGS
from ..context import get_cli_context

logger = logging.getLogger(__name__)

_TYPE_MAP: dict[str, int] = {
    "REG_SZ": 1,
    "REG_EXPAND_SZ": 2,
    "REG_BINARY": 3,
    "REG_DWORD": 4,
    "REG_QWORD": 11,
    "REG_MULTI_SZ": 7,
    "REG_NONE": 0,
}

_TYPE_NAMES: dict[int, str] = {v: k for k, v in _TYPE_MAP.items()}


def _resolve_db_path(ctx: click.Context, db_option: str | None) -> Path:
    """Resolve the database path from --db option or config."""
    if db_option:
        return Path(db_option)

    try:
        cli_ctx = get_cli_context(ctx)
        config = cli_ctx.config
        registry_section = config.data.get("registry", {})  # type: ignore[union-attr]  # pyright: ignore[reportUnknownMemberType]
        db_path_str = str(registry_section.get("db_path", "")) if isinstance(registry_section, dict) else ""  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        if db_path_str:
            return Path(db_path_str)  # pyright: ignore[reportUnknownArgumentType]
    except (AttributeError, KeyError, RuntimeError):
        pass

    raise click.UsageError(
        "No registry database specified. Use --db PATH or configure registry.db_path "
        "in config (--set registry.db_path=PATH or REGISTRY__DB_PATH in .env)."
    )


def _parse_key_path(key_path: str) -> tuple[str, str]:
    """Split a full key path into (hive_name, sub_path).

    >>> _parse_key_path(r"HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft")
    ('HKEY_LOCAL_MACHINE', 'SOFTWARE\\\\Microsoft')
    """
    parts = key_path.split("\\", 1)
    hive_name = parts[0]
    sub_path = parts[1] if len(parts) > 1 else ""
    return hive_name, sub_path


def _get_backend_and_key(db_path: Path, key_path: str):  # type: ignore[no-untyped-def]
    """Open a SqliteBackend and resolve the key path to a FakeRegistryKey."""
    from fake_winreg.adapters.persistence.sqlite_backend import SqliteBackend
    from fake_winreg.domain.constants import hive_name_hashed_by_int

    hive_name, sub_path = _parse_key_path(key_path)

    hive_int_map = {name: key for key, name in hive_name_hashed_by_int.items()}
    hive_int = hive_int_map.get(hive_name)
    if hive_int is None:
        raise click.UsageError(f"Unknown hive: {hive_name}")

    backend = SqliteBackend(db_path)
    hive_key = backend.get_hive(hive_int)

    if sub_path:
        try:
            reg_key = backend.get_key(hive_key, sub_path)
        except FileNotFoundError:
            backend.close()
            raise click.UsageError(f"Key not found: {key_path}")
    else:
        reg_key = hive_key

    return backend, reg_key


def _format_value_data(data: None | bytes | int | str | list[str], value_type: int) -> str:
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


@click.group("reg", context_settings=CLICK_CONTEXT_SETTINGS)
@click.option("--db", "db_path", default=None, type=click.Path(), help="Path to SQLite registry database.")
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
    ctx.ensure_object(dict)
    ctx.obj["reg_db"] = db_path


def _get_db_path(ctx: click.Context) -> Path:
    """Get the DB path from the reg group's --db option or config."""
    db_option: str | None = ctx.obj.get("reg_db") if isinstance(ctx.obj, dict) else None  # type: ignore[union-attr]  # pyright: ignore[reportUnknownMemberType]
    return _resolve_db_path(ctx, db_option)  # pyright: ignore[reportUnknownArgumentType]


# ---------------------------------------------------------------------------
# Key commands
# ---------------------------------------------------------------------------


@cli_reg.command("list-keys", context_settings=CLICK_CONTEXT_SETTINGS)
@click.argument("key_path")
@click.pass_context
def cli_reg_list_keys(ctx: click.Context, key_path: str) -> None:
    """List subkeys of a registry key.

    \b
    Example:
      fake-winreg reg --db my.db list-keys HKEY_LOCAL_MACHINE\\SOFTWARE
    """
    db_path = _get_db_path(ctx)
    backend, reg_key = _get_backend_and_key(db_path, key_path)
    try:
        for name in backend.enum_keys(reg_key):
            click.echo(name)
    finally:
        backend.close()


@cli_reg.command("create-key", context_settings=CLICK_CONTEXT_SETTINGS)
@click.argument("key_path")
@click.pass_context
def cli_reg_create_key(ctx: click.Context, key_path: str) -> None:
    """Create a registry key (and intermediate parents).

    \b
    Example:
      fake-winreg reg --db my.db create-key HKEY_LOCAL_MACHINE\\SOFTWARE\\MyApp
    """
    from fake_winreg.adapters.persistence.sqlite_backend import SqliteBackend
    from fake_winreg.domain.constants import hive_name_hashed_by_int

    db_path = _get_db_path(ctx)
    hive_name, sub_path = _parse_key_path(key_path)

    if not sub_path:
        raise click.UsageError("Cannot create a root hive key.")

    hive_int_map = {name: key for key, name in hive_name_hashed_by_int.items()}
    hive_int = hive_int_map.get(hive_name)
    if hive_int is None:
        raise click.UsageError(f"Unknown hive: {hive_name}")

    backend = SqliteBackend(db_path)
    try:
        hive_key = backend.get_hive(hive_int)
        backend.create_key(hive_key, sub_path)
    finally:
        backend.close()


@cli_reg.command("delete-key", context_settings=CLICK_CONTEXT_SETTINGS)
@click.argument("key_path")
@click.pass_context
def cli_reg_delete_key(ctx: click.Context, key_path: str) -> None:
    """Delete a registry key (must have no subkeys).

    \b
    Example:
      fake-winreg reg --db my.db delete-key HKEY_LOCAL_MACHINE\\SOFTWARE\\MyApp
    """
    from fake_winreg.adapters.persistence.sqlite_backend import SqliteBackend
    from fake_winreg.domain.constants import hive_name_hashed_by_int

    db_path = _get_db_path(ctx)
    hive_name, sub_path = _parse_key_path(key_path)

    if not sub_path:
        raise click.UsageError("Cannot delete a root hive key.")

    hive_int_map = {name: key for key, name in hive_name_hashed_by_int.items()}
    hive_int = hive_int_map.get(hive_name)
    if hive_int is None:
        raise click.UsageError(f"Unknown hive: {hive_name}")

    backend = SqliteBackend(db_path)
    try:
        hive_key = backend.get_hive(hive_int)
        backend.delete_key(hive_key, sub_path)
    except FileNotFoundError:
        raise click.UsageError(f"Key not found: {key_path}")
    except PermissionError:
        raise click.UsageError(f"Cannot delete key with subkeys: {key_path}")
    finally:
        backend.close()


@cli_reg.command("info", context_settings=CLICK_CONTEXT_SETTINGS)
@click.argument("key_path")
@click.pass_context
def cli_reg_info(ctx: click.Context, key_path: str) -> None:
    """Show key information (subkey count, value count, last modified).

    \b
    Example:
      fake-winreg reg --db my.db info HKEY_LOCAL_MACHINE\\SOFTWARE
    """
    db_path = _get_db_path(ctx)
    backend, reg_key = _get_backend_and_key(db_path, key_path)
    try:
        n_subkeys, n_values, last_mod = backend.query_info(reg_key)
        click.echo(f"Subkeys: {n_subkeys}")
        click.echo(f"Values:  {n_values}")
        click.echo(f"Last modified: {last_mod}")
    finally:
        backend.close()


# ---------------------------------------------------------------------------
# Value commands
# ---------------------------------------------------------------------------


@cli_reg.command("list-values", context_settings=CLICK_CONTEXT_SETTINGS)
@click.argument("key_path")
@click.pass_context
def cli_reg_list_values(ctx: click.Context, key_path: str) -> None:
    """List all values in a registry key.

    \b
    Example:
      fake-winreg reg --db my.db list-values HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion
    """
    db_path = _get_db_path(ctx)
    backend, reg_key = _get_backend_and_key(db_path, key_path)
    try:
        values = backend.enum_values(reg_key)
        if not values:
            return
        name_width = max(len(v[0]) or 9 for v in values)  # 9 = len("(Default)")
        for vname, vdata, vtype in values:
            display_name = vname if vname else "(Default)"
            type_name = _TYPE_NAMES.get(vtype, f"REG_({vtype})")
            display_data = _format_value_data(vdata, vtype)
            click.echo(f"{display_name:<{name_width}}  {type_name:<14}  {display_data}")
    finally:
        backend.close()


@cli_reg.command("get", context_settings=CLICK_CONTEXT_SETTINGS)
@click.argument("key_path")
@click.argument("value_name")
@click.pass_context
def cli_reg_get(ctx: click.Context, key_path: str, value_name: str) -> None:
    """Get a specific registry value.

    \b
    Example:
      fake-winreg reg --db my.db get HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion CurrentBuild
    """
    db_path = _get_db_path(ctx)
    backend, reg_key = _get_backend_and_key(db_path, key_path)
    try:
        fval = backend.get_value(reg_key, value_name)
        click.echo(_format_value_data(fval.value, fval.value_type))
    except (KeyError, FileNotFoundError):
        raise click.UsageError(f"Value not found: {value_name}")
    finally:
        backend.close()


@cli_reg.command("set", context_settings=CLICK_CONTEXT_SETTINGS)
@click.argument("key_path")
@click.argument("value_name")
@click.argument("data")
@click.option("--type", "reg_type", default="REG_SZ", help="Registry type (REG_SZ, REG_DWORD, REG_BINARY, etc.)")
@click.pass_context
def cli_reg_set(ctx: click.Context, key_path: str, value_name: str, data: str, reg_type: str) -> None:
    """Set a registry value.

    \b
    Examples:
      fake-winreg reg --db my.db set HKEY_LOCAL_MACHINE\\SOFTWARE\\MyApp Name "hello"
      fake-winreg reg --db my.db set HKEY_LOCAL_MACHINE\\SOFTWARE\\MyApp Count 42 --type REG_DWORD
      fake-winreg reg --db my.db set HKEY_LOCAL_MACHINE\\SOFTWARE\\MyApp Data deadbeef --type REG_BINARY
      fake-winreg reg --db my.db set HKEY_LOCAL_MACHINE\\SOFTWARE\\MyApp List "a,b,c" --type REG_MULTI_SZ
    """
    from fake_winreg.adapters.persistence.sqlite_backend import SqliteBackend
    from fake_winreg.domain.constants import hive_name_hashed_by_int

    type_int = _TYPE_MAP.get(reg_type.upper())
    if type_int is None:
        valid = ", ".join(sorted(_TYPE_MAP.keys()))
        raise click.UsageError(f"Unknown type: {reg_type}. Valid types: {valid}")

    parsed_data = _parse_value_data(data, type_int)

    db_path = _get_db_path(ctx)
    hive_name, sub_path = _parse_key_path(key_path)

    hive_int_map = {name: key for key, name in hive_name_hashed_by_int.items()}
    hive_int = hive_int_map.get(hive_name)
    if hive_int is None:
        raise click.UsageError(f"Unknown hive: {hive_name}")

    backend = SqliteBackend(db_path)
    try:
        hive_key = backend.get_hive(hive_int)
        reg_key = backend.create_key(hive_key, sub_path) if sub_path else hive_key
        backend.set_value(reg_key, value_name, parsed_data, type_int)
    finally:
        backend.close()


@cli_reg.command("delete-value", context_settings=CLICK_CONTEXT_SETTINGS)
@click.argument("key_path")
@click.argument("value_name")
@click.pass_context
def cli_reg_delete_value(ctx: click.Context, key_path: str, value_name: str) -> None:
    """Delete a registry value.

    \b
    Example:
      fake-winreg reg --db my.db delete-value HKEY_LOCAL_MACHINE\\SOFTWARE\\MyApp MyValue
    """
    db_path = _get_db_path(ctx)
    backend, reg_key = _get_backend_and_key(db_path, key_path)
    try:
        backend.delete_value(reg_key, value_name)
    except (KeyError, FileNotFoundError):
        raise click.UsageError(f"Value not found: {value_name}")
    finally:
        backend.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_value_data(data: str, reg_type: int) -> None | bytes | int | str | list[str]:
    """Parse string input into the appropriate Python type for the registry."""
    from fake_winreg.domain.constants import (
        REG_BINARY,
        REG_DWORD,
        REG_EXPAND_SZ,
        REG_MULTI_SZ,
        REG_NONE,
        REG_QWORD,
        REG_SZ,
    )

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
