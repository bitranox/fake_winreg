"""Import and export functions for Windows .reg file format.

Supports Registry Editor Version 5.00 format — the same format produced
by Windows ``regedit.exe`` when exporting keys.
"""

from __future__ import annotations

import re
import struct
from collections.abc import Callable
from pathlib import Path

from fake_winreg.application.ports import RegistryBackend
from fake_winreg.domain.api import _get_backend  # pyright: ignore[reportPrivateUsage]
from fake_winreg.domain.constants import (
    REG_BINARY,
    REG_DWORD,
    REG_EXPAND_SZ,
    REG_MULTI_SZ,
    REG_NONE,
    REG_QWORD,
    REG_SZ,
    hive_name_hashed_by_int,
)
from fake_winreg.domain.registry import FakeRegistryKey

_REG_FILE_HEADER = "Windows Registry Editor Version 5.00"
_REGEDIT4_HEADER = "REGEDIT4"
_LINE_WRAP_LIMIT = 80

# Reverse mapping: hive name string -> hive integer constant
_HIVE_NAME_TO_INT: dict[str, int] = {name: key for key, name in hive_name_hashed_by_int.items()}

# hex(N) type code -> REG_* constant
_HEX_TYPE_MAP: dict[int, int] = {
    0: REG_NONE,
    2: REG_EXPAND_SZ,
    3: REG_BINARY,
    7: REG_MULTI_SZ,
    11: REG_QWORD,
}

# Patterns for parsing .reg lines
_RE_KEY_LINE = re.compile(r"^\[(-?)(HKEY_\w+)(?:\\(.+))?\]$")
_RE_DEFAULT_VALUE = re.compile(r"^@=(.+)$")
_RE_NAMED_VALUE = re.compile(r'^"((?:[^"\\]|\\.)*)"\s*=\s*(.+)$')
_RE_DWORD = re.compile(r"^dword:([0-9a-fA-F]{1,8})$")
_RE_HEX_TYPED = re.compile(r"^hex(?:\(([0-9a-fA-F]+)\))?:(.*)$")


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------


def import_reg(path: str | Path, *, encoding: str | None = None) -> None:
    """Import a Windows .reg file into the currently active backend.

    Args:
        path: Path to the .reg file.
        encoding: Force a specific encoding. If None (default), auto-detects
            from BOM: UTF-16 LE if BOM ``FF FE`` is present, otherwise UTF-8.
    """
    path = Path(path)
    if encoding is None:
        encoding = _detect_reg_encoding(path)
    raw_text = path.read_text(encoding=encoding)
    lines = _join_continuation_lines(raw_text.splitlines())
    backend = _get_backend()

    current_key: FakeRegistryKey | None = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        if line in (_REG_FILE_HEADER, _REGEDIT4_HEADER):
            continue

        key_match = _RE_KEY_LINE.match(line)
        if key_match:
            current_key = _handle_key_line(key_match, backend)
            continue

        if current_key is None:
            continue

        default_match = _RE_DEFAULT_VALUE.match(line)
        if default_match:
            _handle_value_assignment("", default_match.group(1), current_key, backend)
            continue

        named_match = _RE_NAMED_VALUE.match(line)
        if named_match:
            value_name = _unescape_reg_string(named_match.group(1))
            _handle_value_assignment(value_name, named_match.group(2), current_key, backend)


def _join_continuation_lines(lines: list[str]) -> list[str]:
    """Join lines ending with backslash continuation."""
    result: list[str] = []
    current = ""
    for raw_line in lines:
        if current:
            raw_line = raw_line.lstrip()
        current += raw_line
        if current.endswith("\\"):
            current = current[:-1]
        else:
            result.append(current)
            current = ""
    if current:
        result.append(current)
    return result


def _handle_key_line(match: re.Match[str], backend: RegistryBackend) -> FakeRegistryKey | None:
    """Process a key header line, returning the created/opened key or None."""
    delete_flag = match.group(1)
    hive_name = match.group(2)
    sub_path = match.group(3) or ""

    hive_int = _HIVE_NAME_TO_INT.get(hive_name)
    if hive_int is None:
        return None
    hive_root = backend.get_hive(hive_int)

    if delete_flag == "-":
        if sub_path:
            try:
                backend.delete_key(hive_root, sub_path)
            except (FileNotFoundError, PermissionError):
                pass
        return None

    if sub_path:
        return backend.create_key(hive_root, sub_path)
    return hive_root


def _handle_value_assignment(
    value_name: str,
    raw_data: str,
    current_key: FakeRegistryKey,
    backend: RegistryBackend,
) -> None:
    """Parse and store a single value assignment."""
    raw_data = raw_data.strip()

    # Delete value
    if raw_data == "-":
        try:
            backend.delete_value(current_key, value_name)
        except (FileNotFoundError, KeyError):
            pass
        return

    # REG_SZ string value
    if raw_data.startswith('"') and raw_data.endswith('"'):
        string_value = _unescape_reg_string(raw_data[1:-1])
        backend.set_value(current_key, value_name, string_value, REG_SZ)
        return

    # DWORD
    dword_match = _RE_DWORD.match(raw_data)
    if dword_match:
        int_value = int(dword_match.group(1), 16)
        backend.set_value(current_key, value_name, int_value, REG_DWORD)
        return

    # hex, hex(N)
    hex_match = _RE_HEX_TYPED.match(raw_data)
    if hex_match:
        type_code_str = hex_match.group(1)
        hex_data_str = hex_match.group(2).strip()
        _handle_hex_value(value_name, type_code_str, hex_data_str, current_key, backend)


def _handle_hex_value(
    value_name: str,
    type_code_str: str | None,
    hex_data_str: str,
    current_key: FakeRegistryKey,
    backend: RegistryBackend,
) -> None:
    """Parse a hex(...) value and store it."""
    if type_code_str is None:
        reg_type = REG_BINARY
    else:
        type_code = int(type_code_str, 16)
        reg_type = _HEX_TYPE_MAP.get(type_code, type_code)

    raw_bytes = _parse_hex_bytes(hex_data_str)

    value = _decode_hex_value(reg_type, raw_bytes)
    backend.set_value(current_key, value_name, value, reg_type)


def _parse_hex_bytes(hex_str: str) -> bytes:
    """Parse comma-separated hex byte string into bytes."""
    hex_str = hex_str.strip().rstrip(",")
    if not hex_str:
        return b""
    parts = [p.strip() for p in hex_str.split(",")]
    return bytes(int(h, 16) for h in parts if h)


def _decode_utf16le_string(data: bytes) -> str:
    """Decode UTF-16 LE bytes to string, stripping trailing null."""
    text = data.decode("utf-16-le", errors="replace")
    return text.rstrip("\x00")


def _decode_utf16le_multi_string(data: bytes) -> list[str]:
    """Decode UTF-16 LE multi-string (null-separated, double-null terminated)."""
    text = data.decode("utf-16-le", errors="replace")
    text = text.rstrip("\x00")
    if not text:
        return []
    return text.split("\x00")


_HEX_DECODERS: dict[int, Callable[[bytes], None | bytes | int | str | list[str]]] = {
    REG_EXPAND_SZ: _decode_utf16le_string,
    REG_MULTI_SZ: _decode_utf16le_multi_string,
    REG_QWORD: lambda b: struct.unpack("<Q", b)[0] if len(b) == 8 else (b or None),
    REG_NONE: lambda b: b or None,
    REG_BINARY: lambda b: b,
}


def _decode_hex_value(reg_type: int, raw_bytes: bytes) -> None | bytes | int | str | list[str]:
    """Decode raw bytes into the appropriate Python value for the given type."""
    decoder = _HEX_DECODERS.get(reg_type)
    if decoder is not None:
        return decoder(raw_bytes)
    return raw_bytes


def _unescape_reg_string(s: str) -> str:
    """Unescape a .reg file string value (reverse of _escape_reg_string)."""
    return s.replace("\\n", "\n").replace("\\r", "\r").replace('\\"', '"').replace("\\\\", "\\")


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def export_reg(
    path: str | Path,
    hives: list[str] | None = None,
    *,
    encoding: str = "utf-16-le",
    version: int = 5,
) -> None:
    """Export the active backend's state to a .reg file.

    Args:
        path: Output file path.
        hives: Optional list of hive names to export. None exports all.
        encoding: File encoding. Default ``"utf-16-le"`` produces files
            compatible with Windows ``regedit.exe`` (with BOM). Use
            ``"utf-8"`` for human-readable / cross-platform files.
        version: Registry file format version. ``5`` (default) writes
            ``Windows Registry Editor Version 5.00`` header. ``4`` writes
            ``REGEDIT4`` header with ANSI encoding.
    """
    path = Path(path)
    backend = _get_backend()

    if version == 4:
        header = _REGEDIT4_HEADER
        if encoding == "utf-16-le":
            encoding = "ascii"
    else:
        header = _REG_FILE_HEADER

    lines: list[str] = [header, ""]

    target_hives = _resolve_target_hives(hives)

    for hive_int, hive_name in sorted(hive_name_hashed_by_int.items(), key=lambda kv: kv[1]):
        if hive_name not in target_hives:
            continue
        hive_root = backend.get_hive(hive_int)
        _export_key_recursive(hive_root, hive_name, lines, backend)

    content = "\r\n".join(lines) + "\r\n"
    if encoding.lower().replace("-", "") in ("utf16le", "utf16"):
        path.write_bytes(b"\xff\xfe" + content.encode("utf-16-le"))
    else:
        path.write_text(content, encoding=encoding)


def _resolve_target_hives(hives: list[str] | None) -> set[str]:
    """Return the set of hive names to export."""
    if hives is None:
        return set(hive_name_hashed_by_int.values())
    return set(hives)


def _export_key_recursive(
    key: FakeRegistryKey,
    full_path: str,
    lines: list[str],
    backend: RegistryBackend,
) -> None:
    """Recursively export a key and all its subkeys."""
    lines.append(f"[{full_path}]")
    _export_values(key, lines, backend)
    lines.append("")

    for subkey_name in sorted(backend.enum_keys(key)):
        child = backend.get_key(key, subkey_name)
        _export_key_recursive(child, f"{full_path}\\{subkey_name}", lines, backend)


def _export_values(key: FakeRegistryKey, lines: list[str], backend: RegistryBackend) -> None:
    """Export all values of a single key."""

    values = sorted(backend.enum_values(key), key=lambda t: t[0])
    for value_name, value_data, value_type in values:
        _export_single_value(value_name, value_data, value_type, lines)


def _export_single_value(
    value_name: str,
    value_data: None | bytes | int | str | list[str],
    value_type: int,
    lines: list[str],
) -> None:
    """Format and append a single value line."""
    name_prefix = _format_value_name(value_name)

    if value_type == REG_SZ:
        escaped = _escape_reg_string(str(value_data) if value_data is not None else "")
        lines.append(f'{name_prefix}"{escaped}"')
    elif value_type == REG_DWORD:
        int_val = value_data if isinstance(value_data, int) else 0
        lines.append(f"{name_prefix}dword:{int_val:08x}")
    else:
        hex_prefix, hex_bytes = _encode_typed_hex(value_data, value_type)
        formatted = _format_hex_line(name_prefix, hex_prefix, hex_bytes)
        lines.append(formatted)


def _format_value_name(value_name: str) -> str:
    """Return the name prefix for a .reg value line."""
    if value_name == "":
        return "@="
    escaped = _escape_reg_string(value_name)
    return f'"{escaped}"='


def _escape_reg_string(s: str) -> str:
    """Escape a string for .reg file output."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


def _encode_typed_hex(
    value_data: None | bytes | int | str | list[str],
    value_type: int,
) -> tuple[str, bytes]:
    """Return (hex_type_prefix, raw_bytes) for a hex-encoded value."""
    raw_bytes = _value_to_bytes(value_data, value_type)

    if value_type == REG_BINARY:
        return "hex:", raw_bytes
    return f"hex({value_type:x}):", raw_bytes


def _value_to_bytes(
    value_data: None | bytes | int | str | list[str],
    value_type: int,
) -> bytes:
    """Convert a value to its raw byte representation."""
    if value_data is None:
        return b""

    if value_type == REG_EXPAND_SZ:
        return _encode_utf16le_string(str(value_data))
    if value_type == REG_MULTI_SZ:
        string_list = value_data if isinstance(value_data, list) else []
        return _encode_utf16le_multi_string(string_list)
    if value_type == REG_QWORD:
        int_val = value_data if isinstance(value_data, int) else 0
        return struct.pack("<Q", int_val)
    if isinstance(value_data, bytes):
        return value_data
    if isinstance(value_data, int):
        return struct.pack("<I", value_data)
    if isinstance(value_data, str):
        return value_data.encode("utf-16-le") + b"\x00\x00"
    return b""


def _encode_utf16le_string(s: str) -> bytes:
    """Encode string as UTF-16 LE with null terminator."""
    return s.encode("utf-16-le") + b"\x00\x00"


def _encode_utf16le_multi_string(strings: list[str]) -> bytes:
    """Encode multi-string as UTF-16 LE (null-separated, double-null terminated)."""
    parts: list[bytes] = []
    for s in strings:
        parts.append(s.encode("utf-16-le") + b"\x00\x00")
    parts.append(b"\x00\x00")  # final double-null
    return b"".join(parts)


def _format_hex_line(name_prefix: str, hex_prefix: str, raw_bytes: bytes) -> str:
    """Format a hex value line with wrapping at _LINE_WRAP_LIMIT chars."""
    if not raw_bytes:
        return f"{name_prefix}{hex_prefix}"

    hex_parts = [f"{b:02x}" for b in raw_bytes]
    full_prefix = f"{name_prefix}{hex_prefix}"

    # Build wrapped output
    result = full_prefix
    current_len = len(full_prefix)
    for i, part in enumerate(hex_parts):
        separator = "," if i < len(hex_parts) - 1 else ""
        addition = part + separator
        if current_len + len(addition) > _LINE_WRAP_LIMIT:
            result += "\\\r\n  "
            current_len = 2
        result += addition
        current_len += len(addition)

    return result


def _detect_reg_encoding(path: Path) -> str:
    """Auto-detect .reg file encoding from BOM.

    Returns ``"utf-16-le"`` if the file starts with the UTF-16 LE BOM
    (``FF FE``), otherwise ``"utf-8-sig"`` (handles optional UTF-8 BOM).
    """
    raw = path.read_bytes()[:4]
    if raw[:2] == b"\xff\xfe":
        return "utf-16"  # utf-16 codec auto-strips BOM
    return "utf-8-sig"


__all__ = ["import_reg", "export_reg"]
