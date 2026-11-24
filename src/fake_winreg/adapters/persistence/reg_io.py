"""Import and export functions for Windows .reg file format.

Supports Registry Editor Version 5.00 format - the same format produced
by Windows ``regedit.exe`` when exporting keys.
"""

from __future__ import annotations

import codecs
import os
import re
import shutil
import struct
import tempfile
from collections import deque
from enum import IntEnum
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, NamedTuple

from fake_winreg.domain.api import get_backend
from fake_winreg.domain.constants import (
    REG_BINARY,
    REG_DWORD,
    REG_EXPAND_SZ,
    REG_MULTI_SZ,
    REG_NONE,
    REG_QWORD,
    REG_SZ,
    hive_int_by_name,
    hive_name_hashed_by_int,
)

if TYPE_CHECKING:
    from codecs import IncrementalEncoder
    from collections.abc import Callable, Iterable, Iterator, Mapping
    from typing import BinaryIO

    from fake_winreg.application.ports import RegistryBackend
    from fake_winreg.domain.registry import FakeRegistryKey
    from fake_winreg.domain.types import RegData

_REG_FILE_HEADER = "Windows Registry Editor Version 5.00"
_REGEDIT4_HEADER = "REGEDIT4"
_LINE_WRAP_LIMIT = 80
_LINE_END = "\r\n"
_UTF16_BOM = b"\xff\xfe"
# Canonical codec names (codecs.lookup(...).name) export_reg writes as UTF-16 LE plus a BOM.
_UTF16_CODEC_NAMES: Final = frozenset({"utf-16", "utf-16-le"})

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
    _require_decodable(path, encoding)
    backend = get_backend()
    # Iterate the open file instead of read_text + splitlines, so only one
    # logical line is held at a time. File iteration splits on \n, \r and \r\n
    # only, which is all a .reg file uses; splitlines also split inside values
    # on \x0b, \x0c, \x1c-\x1e, \x85, U+2028 and U+2029.
    with path.open(encoding=encoding) as reg_file:
        _import_lines(_join_continuation_lines(_strip_line_ends(reg_file)), backend)


def _require_decodable(path: Path, encoding: str) -> None:
    """Decode the whole file once and discard the text, so a bad byte raises before any write.

    The import writes each key as it reads it, so without this pass an
    undecodable byte near the end would leave every key before it imported. It
    reads the file the same way the import does, one line at a time, so memory
    stays flat at the cost of reading the file twice.

    Raises:
        UnicodeDecodeError: If the file is not valid in *encoding*.
    """
    with path.open(encoding=encoding) as reg_file:
        deque(reg_file, maxlen=0)


def _import_lines(lines: Iterable[str], backend: RegistryBackend) -> None:
    """Apply each logical .reg line to *backend*, tracking the current key."""
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


def _strip_line_ends(raw_lines: Iterable[str]) -> Iterator[str]:
    """Yield each physical line without its terminator (universal newlines leave only \\n)."""
    for raw_line in raw_lines:
        yield raw_line.removesuffix("\n")


def _join_continuation_lines(lines: Iterable[str]) -> Iterator[str]:
    """Yield logical lines, joining a line ending with a backslash to the next one."""
    current = ""
    for raw_line in lines:
        if current:
            raw_line = raw_line.lstrip()
        current += raw_line
        if current.endswith("\\"):
            current = current[:-1]
        else:
            yield current
            current = ""
    if current:
        yield current


def _handle_key_line(match: re.Match[str], backend: RegistryBackend) -> FakeRegistryKey | None:
    """Process a key header line, returning the created/opened key or None."""
    delete_flag = match.group(1)
    hive_name = match.group(2)
    sub_path = match.group(3) or ""

    hive_int = hive_int_by_name.get(hive_name)
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
    # hex(N) names the REG_* type by its number, so the code is the type.
    reg_type = REG_BINARY if type_code_str is None else int(type_code_str, 16)

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


_HEX_DECODERS: Final[Mapping[int, Callable[[bytes], RegData]]] = MappingProxyType(
    {
        REG_EXPAND_SZ: _decode_utf16le_string,
        REG_MULTI_SZ: _decode_utf16le_multi_string,
        REG_QWORD: lambda b: struct.unpack("<Q", b)[0] if len(b) == 8 else (b or None),
        REG_NONE: lambda b: b or None,
        REG_BINARY: lambda b: b,
    }
)


def _decode_hex_value(reg_type: int, raw_bytes: bytes) -> RegData:
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

    Raises:
        OSError: If copying the finished export over an existing *path* stops
            partway. *path* may then be incomplete; the complete export is kept
            in a temp file whose path the message names.
    """
    path = Path(path)
    backend = get_backend()
    file_format = _resolve_file_format(encoding, _RegVersion.parse(version))
    # Looked up before the file is opened, so an unknown codec leaves no file behind.
    encoder = codecs.getincrementalencoder(file_format.codec)()
    lines = _iter_export_lines(backend, file_format.header, _resolve_target_hives(hives))

    # Exclusive creation instead of an exists() check: a file created between
    # the check and the open, or a dangling symlink (O_EXCL never follows one),
    # would otherwise count as new and be deleted if the export failed.
    try:
        new_file = path.open("xb")
    except FileExistsError:
        _export_over_existing(path, file_format.bom, encoder, lines)
        return
    _export_to_new(path, new_file, file_format.bom, encoder, lines)


def _export_to_new(
    path: Path, reg_file: BinaryIO, bom: bytes, encoder: IncrementalEncoder, lines: Iterable[str]
) -> None:
    """Write into the file this export just created at *path*; remove it again on failure."""
    try:
        with reg_file:
            _write_reg_lines(reg_file, bom, encoder, lines)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _export_over_existing(path: Path, bom: bytes, encoder: IncrementalEncoder, lines: Iterable[str]) -> None:
    """Export into a temp file, then copy its bytes into *path*.

    A failure partway (a value the codec cannot encode) must leave the existing
    file as it was, so nothing touches it until the whole export succeeded.
    The bytes are copied into the existing file instead of renaming the temp
    file over it: a rename would replace the file's own permissions, ACL,
    extended attributes and hard links with the temp file's.

    Once the target is opened it is truncated, so from then on the temp file
    holds the only complete export: a copy-back that fails (a full disk, an
    interrupt) keeps it, and an OSError names where it is.
    """
    temp = _create_temp_file(path)
    temp_path = temp.path
    with os.fdopen(temp.handle, "w+b") as temp_file:
        try:
            _write_reg_lines(temp_file, bom, encoder, lines)
            temp_file.seek(0)
            target = path.open("wb")
        except BaseException:
            # The target is untouched, so the temp file holds nothing worth keeping.
            # Closed first: Windows cannot delete a file that is still open.
            try:
                temp_file.close()
            finally:
                temp_path.unlink(missing_ok=True)
            raise
        _copy_back(temp_file, target, path, temp_path)
    temp_path.unlink(missing_ok=True)


class _TempFile(NamedTuple):
    """An open temp file's OS descriptor and its path."""

    handle: int
    path: Path


def _create_temp_file(path: Path) -> _TempFile:
    """Create the export's temp file beside *path*, or in the system temp dir if that is refused.

    Beside the target is preferred: the export then takes space on the target's
    own filesystem, and a temp file kept after a failed copy-back sits next to
    the file it belongs to. Because the bytes are copied back rather than
    renamed, the temp file may live anywhere, so a writable file in a read-only
    directory can still be exported over. mkstemp makes the file readable by
    its owner only, which matters in a shared temp dir.
    """
    prefix = f".{path.name}."
    try:
        handle, temp_name = tempfile.mkstemp(dir=path.parent, prefix=prefix, suffix=".tmp")
    except PermissionError:
        handle, temp_name = tempfile.mkstemp(prefix=prefix, suffix=".tmp")
    return _TempFile(handle=handle, path=Path(temp_name))


def _copy_back(temp_file: BinaryIO, target: BinaryIO, path: Path, temp_path: Path) -> None:
    """Copy the finished export into the opened *target*, keeping the temp file on failure.

    Raises:
        OSError: The copy failed partway; the message names the kept temp file.
            The errno is the original one, so ``except OSError`` subclasses such
            as ``PermissionError`` still match. An interrupt is re-raised as it is.
    """
    try:
        with target:
            # Chunked copy, so memory stays flat however large the export.
            shutil.copyfileobj(temp_file, target)
    except OSError as error:
        raise _copy_back_error(error, path, temp_path) from error


def _copy_back_error(error: OSError, path: Path, temp_path: Path) -> OSError:
    """Build the error for a copy-back that stopped partway, naming the kept temp file."""
    message = f"{error.strerror or error}: writing {path} stopped partway; the complete export is kept in {temp_path}"
    if error.errno is None:
        return OSError(message)
    return OSError(error.errno, message)


def _write_reg_lines(reg_file: BinaryIO, bom: bytes, encoder: IncrementalEncoder, lines: Iterable[str]) -> None:
    """Encode and write each line as it is produced, so memory stays at one line.

    An incremental encoder writes a codec's own BOM (utf-8-sig) once, exactly as
    encoding the whole text did. Binary mode keeps \\r\\n as written on Windows,
    where text mode would translate it.
    """
    reg_file.write(bom)
    for line in lines:
        reg_file.write(encoder.encode(line + _LINE_END))
    reg_file.write(encoder.encode("", final=True))


class _RegVersion(IntEnum):
    """The two .reg file format versions regedit writes."""

    REGEDIT4 = 4
    V5 = 5

    @classmethod
    def parse(cls, version: int) -> _RegVersion:
        """Map export_reg's ``version`` argument: 4 is REGEDIT4, anything else version 5."""
        return cls.REGEDIT4 if version == cls.REGEDIT4 else cls.V5


class _RegFileFormat(NamedTuple):
    """How export_reg writes a file: the header line, the text codec, and a BOM written before it."""

    header: str
    codec: str
    bom: bytes


def _resolve_file_format(encoding: str, version: _RegVersion) -> _RegFileFormat:
    """Decide header, codec and BOM once from export_reg's arguments.

    >>> _resolve_file_format("utf-16-le", _RegVersion.REGEDIT4)
    _RegFileFormat(header='REGEDIT4', codec='ascii', bom=b'')
    >>> _resolve_file_format("UTF-16", _RegVersion.V5).bom
    b'\\xff\\xfe'
    >>> _resolve_file_format("utf_16_le", _RegVersion.V5).bom
    b'\\xff\\xfe'
    """
    if version is _RegVersion.REGEDIT4:
        header = _REGEDIT4_HEADER
        # Only the exact default spelling is swapped: REGEDIT4 files are ANSI,
        # and a caller who names an encoding explicitly gets that encoding.
        # Not normalised on purpose: "utf16le" or "UTF-16-LE" with version 4
        # has always written UTF-16, and normalising would turn it into ASCII.
        if encoding == "utf-16-le":
            encoding = "ascii"
    else:
        header = _REG_FILE_HEADER
    if _names_utf16(encoding):
        # regedit writes UTF-16 LE with a BOM; the plain utf-16 codec would pick
        # the platform byte order, so both spellings mean LE plus an explicit BOM.
        return _RegFileFormat(header=header, codec="utf-16-le", bom=_UTF16_BOM)
    return _RegFileFormat(header=header, codec=encoding, bom=b"")


def _names_utf16(encoding: str) -> bool:
    """Tell whether *encoding* names UTF-16 or UTF-16 LE, written as LE with a BOM.

    The codec registry's own name catches every spelling it knows (``utf_16_le``,
    ``UTF-16LE``, ``u16``). The text check before it keeps spellings that only
    it accepts, as earlier releases did, so each still writes the same bytes.

    >>> _names_utf16("utf_16_le"), _names_utf16("utf-16-be"), _names_utf16("no-such-codec")
    (True, False, False)
    """
    if encoding.lower().replace("-", "") in ("utf16le", "utf16"):
        return True
    try:
        return codecs.lookup(encoding).name in _UTF16_CODEC_NAMES
    except LookupError:
        # Not decided here: export_reg's encoder lookup reports the unknown codec.
        return False


def _iter_export_lines(backend: RegistryBackend, header: str, target_hives: set[str]) -> Iterator[str]:
    """Yield every line of the .reg file, without line terminators."""
    yield header
    yield ""
    for hive_int, hive_name in sorted(hive_name_hashed_by_int.items(), key=lambda kv: kv[1]):
        if hive_name not in target_hives:
            continue
        hive_root = backend.get_hive(hive_int)
        yield from _export_key_recursive(hive_root, hive_name, backend)


def _resolve_target_hives(hives: list[str] | None) -> set[str]:
    """Return the set of hive names to export."""
    if hives is None:
        return set(hive_name_hashed_by_int.values())
    return set(hives)


def _export_key_recursive(
    key: FakeRegistryKey,
    full_path: str,
    backend: RegistryBackend,
) -> Iterator[str]:
    """Yield the lines of a key and all its subkeys."""
    yield f"[{full_path}]"
    for entry in sorted(backend.enum_values(key), key=lambda e: e.name):
        yield _format_value_line(entry.name, entry.data, entry.value_type)
    yield ""

    for subkey_name in sorted(backend.enum_keys(key)):
        child = backend.get_key(key, subkey_name)
        yield from _export_key_recursive(child, f"{full_path}\\{subkey_name}", backend)


def _format_value_line(value_name: str, value_data: RegData, value_type: int) -> str:
    """Format one value as its .reg line (a hex value may carry embedded continuations)."""
    name_prefix = _format_value_name(value_name)

    if value_type == REG_SZ:
        escaped = _escape_reg_string(str(value_data) if value_data is not None else "")
        return f'{name_prefix}"{escaped}"'
    if value_type == REG_DWORD:
        int_val = value_data if isinstance(value_data, int) else 0
        return f"{name_prefix}dword:{int_val:08x}"
    return _format_hex_line(name_prefix, _hex_type_prefix(value_type), _value_to_bytes(value_data, value_type))


def _format_value_name(value_name: str) -> str:
    """Return the name prefix for a .reg value line."""
    if value_name == "":
        return "@="
    escaped = _escape_reg_string(value_name)
    return f'"{escaped}"='


def _escape_reg_string(s: str) -> str:
    """Escape a string for .reg file output."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


def _hex_type_prefix(value_type: int) -> str:
    """Return the ``hex:`` / ``hex(N):`` prefix that names a hex-encoded value's type.

    >>> _hex_type_prefix(REG_BINARY), _hex_type_prefix(REG_QWORD)
    ('hex:', 'hex(b):')
    """
    if value_type == REG_BINARY:
        return "hex:"
    return f"hex({value_type:x}):"


def _value_to_bytes(value_data: RegData, value_type: int) -> bytes:
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
            result += "\\" + _LINE_END + "  "
            current_len = 2
        result += addition
        current_len += len(addition)

    return result


def _detect_reg_encoding(path: Path) -> str:
    """Auto-detect .reg file encoding from BOM.

    Returns ``"utf-16-le"`` if the file starts with the UTF-16 LE BOM
    (``FF FE``), otherwise ``"utf-8-sig"`` (handles optional UTF-8 BOM).
    """
    with path.open("rb") as reg_file:
        raw = reg_file.read(2)
    if raw == _UTF16_BOM:
        return "utf-16"  # utf-16 codec auto-strips BOM
    return "utf-8-sig"


__all__ = ["export_reg", "import_reg"]
