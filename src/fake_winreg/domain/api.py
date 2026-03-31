"""Fake winreg API — drop-in replacement for the Windows ``winreg`` module.

All public functions mirror the signatures and behavior of Python's built-in
``winreg`` module so that registry-dependent code can be tested on Linux.

Module-level state (``_registry``) matches the real ``winreg`` module's
implicit global pattern.  Call :func:`load_fake_registry` to install a
pre-populated :class:`FakeRegistry` before using the API functions.
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from typing import TYPE_CHECKING

from ._validators import (
    check_access as _check_access,
)
from ._validators import (
    check_argument_must_be_str_or_none as _check_argument_must_be_str_or_none,
)
from ._validators import (
    check_argument_must_be_type_expected as _check_argument_must_be_type_expected,
)
from ._validators import (
    check_index as _check_index,
)
from ._validators import (
    check_key as _check_key,
)
from ._validators import (
    check_reserved as _check_reserved,
)
from ._validators import (
    check_reserved2 as _check_reserved2,
)
from ._validators import (
    raise_os_error_1010 as _raise_os_error_1010,
)
from .constants import (
    KEY_READ,
    KEY_WOW64_32KEY,
    KEY_WRITE,
    REG_SZ,
)
from .handles import Handle, HKEYType, PyHKEY
from .registry import FakeRegistry
from .test_registries import (
    get_minimal_windows_testregistry,  # noqa: F401  # pyright: ignore[reportUnusedImport] - used in doctests
)
from .types import RegData
from .validation import check_value_type_matches_type

if TYPE_CHECKING:
    from fake_winreg.application.ports import RegistryBackend

# Match real winreg module's ``error`` export (alias for OSError)
error = OSError

_RE_PERCENT_VAR = re.compile(r"%([^%]+)%")

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------
_backend: RegistryBackend | None = None
_network_resolver: Callable[[str], bool] | None = None


def _get_backend() -> RegistryBackend:
    """Return the active backend, creating a default InMemoryBackend if none set."""
    global _backend
    if _backend is None:
        from fake_winreg.domain.memory_backend import InMemoryBackend

        _backend = InMemoryBackend()  # type: ignore[assignment]
    return _backend


def use_backend(backend: RegistryBackend) -> None:
    """Set the active registry backend.

    >>> from fake_winreg.domain.memory_backend import InMemoryBackend
    >>> use_backend(InMemoryBackend())
    """
    global _backend
    _backend = backend


def load_fake_registry(fake_registry: FakeRegistry, /) -> None:
    """Install a FakeRegistry instance (backward compat — wraps in InMemoryBackend)."""
    from fake_winreg.domain.memory_backend import InMemoryBackend

    use_backend(InMemoryBackend(fake_registry))  # type: ignore[arg-type]


def configure_network_resolver(resolver: Callable[[str], bool]) -> None:
    """Set the network resolver used by ConnectRegistry.

    Called by the composition layer to inject the real DNS resolver
    without the domain importing from adapters.
    """
    global _network_resolver
    _network_resolver = resolver


# ---------------------------------------------------------------------------
# Public API functions
# ---------------------------------------------------------------------------


def CloseKey(hkey: int | HKEYType, /) -> None:
    r"""Close a previously opened registry key.

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> hive_key = ConnectRegistry(None, 18446744071562067970)
    >>> CloseKey(18446744071562067970)
    """
    if hkey is not None:  # type: ignore[reportUnnecessaryComparison]
        _check_key(hkey)


def ConnectRegistry(computer_name: str | None, key: Handle, /) -> PyHKEY:
    r"""Establish a connection to a predefined registry handle.

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> ConnectRegistry(None, 18446744071562067970)
    <...PyHKEY object at ...>

    >>> ConnectRegistry('HAL', 18446744071562067970)
    Traceback (most recent call last):
        ...
    OSError: [WinError 1707] The network address is invalid

    >>> ConnectRegistry(None, 42)
    Traceback (most recent call last):
        ...
    OSError: [WinError 6] The handle is invalid
    """
    _check_key(key)

    if computer_name:
        resolver: Callable[[str], bool] = _network_resolver or (lambda _name: False)
        if resolver(computer_name):
            system_error = FileNotFoundError("[WinError 53] The network path was not found")
            system_error.winerror = 53  # type: ignore[attr-defined]
            raise system_error
        else:
            network_error = OSError("[WinError 1707] The network address is invalid")
            network_error.winerror = 1707  # type: ignore[attr-defined]
            raise network_error

    fake_reg_handle = _get_backend().get_hive(key if isinstance(key, int) else int(key))
    return PyHKEY(handle=fake_reg_handle)


def CreateKey(key: Handle, sub_key: str | None, /) -> PyHKEY:
    r"""Create or open a registry key.

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, 18446744071562067969)
    >>> key_handle = CreateKey(reg_handle, r'SOFTWARE\xxxx\yyyy')
    >>> DeleteKey(reg_handle, r'SOFTWARE\xxxx\yyyy')
    >>> DeleteKey(reg_handle, r'SOFTWARE\xxxx')
    """
    l_predefined_hkeys = [
        "HKEY_CLASSES_ROOT",
        "HKEY_CURRENT_CONFIG",
        "HKEY_CURRENT_USER",
        "HKEY_DYN_DATA",
        "HKEY_LOCAL_MACHINE",
        "HKEY_PERFORMANCE_DATA",
        "HKEY_USERS",
    ]

    _check_key(key)
    _check_argument_must_be_str_or_none(2, sub_key)

    key_handle = _resolve_key(key)
    original_access = key_handle._access  # type: ignore[reportPrivateUsage]

    if key_handle.handle.full_key not in l_predefined_hkeys and not sub_key:
        _raise_os_error_1010()

    fake_reg_key = _get_backend().create_key(key_handle.handle, sub_key)
    return PyHKEY(fake_reg_key, access=original_access | KEY_WRITE)


def CreateKeyEx(key: Handle, sub_key: str, reserved: int = 0, access: int = KEY_WRITE, /) -> PyHKEY:
    r"""Create or open a registry key with explicit access control.

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, 18446744071562067969)
    >>> key_handle = CreateKeyEx(reg_handle, r'SOFTWARE\xxxx\yyyy', 0, 131078)
    >>> DeleteKey(reg_handle, r'SOFTWARE\xxxx\yyyy')
    >>> DeleteKey(reg_handle, r'SOFTWARE\xxxx')
    """
    _check_key(key)
    _check_argument_must_be_str_or_none(2, sub_key)
    _check_reserved(reserved)
    _check_access(access)

    if sub_key is None:  # type: ignore[reportUnnecessaryComparison]
        _raise_os_error_1010()

    key_handle = _resolve_key(key)
    resolved_access = key_handle._access  # type: ignore[reportPrivateUsage]
    fake_reg_key = _get_backend().create_key(key_handle.handle, sub_key)
    return PyHKEY(fake_reg_key, access=resolved_access)


def DeleteKey(key: Handle, sub_key: str, /) -> None:
    r"""Delete a registry key (must have no subkeys).

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, 18446744071562067969)
    >>> _ = CreateKey(reg_handle, r'SOFTWARE\xxxx\yyyy\zzz')
    >>> DeleteKey(reg_handle, r'SOFTWARE\xxxx\yyyy\zzz')
    >>> DeleteKey(reg_handle, r'SOFTWARE\xxxx\yyyy')
    >>> DeleteKey(reg_handle, r'SOFTWARE\xxxx')
    """
    _check_key(key)
    _check_argument_must_be_type_expected(arg_number=2, argument=sub_key, type_expected=str)

    sub_key = str(sub_key)
    key_handle = _resolve_key(key)
    _get_backend().delete_key(key_handle.handle, sub_key)


def DeleteKeyEx(
    key: Handle,
    sub_key: str,
    access: int = 256,  # KEY_WOW64_64KEY
    reserved: int = 0,
    /,
) -> None:
    r"""Delete a registry key (64-bit variant).

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, 18446744071562067969)
    >>> _ = CreateKey(reg_handle, r'Software\xxxx\yyyy\zzz')
    >>> DeleteKeyEx(reg_handle, r'Software\xxxx\yyyy\zzz')
    >>> DeleteKeyEx(reg_handle, r'Software\xxxx\yyyy')
    >>> DeleteKeyEx(reg_handle, r'Software\xxxx')
    """
    _check_key(key)
    _check_argument_must_be_type_expected(arg_number=2, argument=sub_key, type_expected=str)
    _check_access(access=access)
    _check_reserved(reserved=reserved)

    if access == KEY_WOW64_32KEY:
        raise NotImplementedError("we only support KEY_WOW64_64KEY")
    DeleteKey(key, sub_key)


def DeleteValue(key: Handle, value: str | None, /) -> None:
    r"""Remove a named value from a registry key.

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, 18446744071562067970)
    >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion')
    >>> SetValueEx(key_handle, 'some_test', 0, 1, 'some_test_value')
    >>> DeleteValue(key_handle, 'some_test')
    """
    _check_key(key)
    _check_argument_must_be_str_or_none(2, value)

    if value is None:
        value = ""

    key_handle = _resolve_key(key)
    _get_backend().delete_value(key_handle.handle, value)


def EnumKey(key: Handle, index: int, /) -> str:
    r"""Enumerate subkeys by index.

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, 18446744071562067970)
    >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList')
    >>> assert isinstance(EnumKey(key_handle, 0), str)
    """
    _check_key(key)
    _check_index(index)

    key_handle = _resolve_key(key)
    keys = _get_backend().enum_keys(key_handle.handle)
    try:
        return keys[index]
    except IndexError:
        error = OSError("[WinError 259] No more data is available")
        error.winerror = 259  # type: ignore[attr-defined]
        raise error


def EnumValue(key: Handle, index: int, /) -> tuple[str, RegData, int]:
    r"""Enumerate values by index, returning (name, data, type).

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, 18446744071562067970)
    >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion')
    >>> EnumValue(key_handle, 0)
    (...)
    """
    _check_key(key)
    _check_index(index)

    key_handle = _resolve_key(key)
    values = _get_backend().enum_values(key_handle.handle)
    try:
        return values[index]
    except IndexError:
        error = OSError("[WinError 259] No more data is available")
        error.winerror = 259  # type: ignore[attr-defined]
        raise error


def OpenKey(
    key: Handle,
    sub_key: str | None,
    reserved: int = 0,
    access: int = KEY_READ,
) -> PyHKEY:
    r"""Open an existing registry key (does NOT create).

    This is one of the few winreg functions that accepts named parameters.

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, 18446744071562067970)
    >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion')
    >>> assert key_handle.handle.full_key == r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
    """
    _check_key(key)
    _check_argument_must_be_str_or_none(arg_number=2, argument=sub_key)
    _check_reserved2(reserved)
    _check_access(access)

    if sub_key is None:
        sub_key = ""

    key_handle = _resolve_key(key)
    reg_key = _get_backend().get_key(key_handle.handle, sub_key)
    return PyHKEY(reg_key, access=access)


def OpenKeyEx(
    key: Handle,
    sub_key: str | None,
    reserved: int = 0,
    access: int = KEY_READ,
) -> PyHKEY:
    r"""Open an existing registry key with explicit access.

    This is one of the few winreg functions that accepts named parameters.

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, 18446744071562067970)
    >>> my_key_handle = OpenKeyEx(reg_handle, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion')
    >>> assert my_key_handle.handle.full_key == r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion'

    >>> with OpenKeyEx(reg_handle, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion') as h:
    ...     assert 'CurrentVersion' in h.handle.full_key
    """
    return OpenKey(key, sub_key, reserved, access)


def QueryInfoKey(key: Handle, /) -> tuple[int, int, int]:
    r"""Return (num_subkeys, num_values, last_modified_timestamp) for a key.

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, 18446744071562067970)
    >>> key_handle = OpenKeyEx(reg_handle, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion')
    >>> new_key = CreateKey(key_handle, 'test_query_info')
    >>> QueryInfoKey(new_key)
    (0, 0, ...)
    >>> DeleteKey(key_handle, 'test_query_info')
    """
    _check_key(key)
    reg_handle = _resolve_key(key)
    return _get_backend().query_info(reg_handle.handle)


def QueryValue(key: Handle, sub_key: str | None, /) -> str:
    r"""Retrieve the default (unnamed) value of a key as string.

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, 18446744071562067969)
    >>> key_handle = CreateKey(reg_handle, r'SOFTWARE\lib_registry_test')
    >>> assert QueryValue(reg_handle, r'SOFTWARE\lib_registry_test') == ''
    >>> DeleteKey(reg_handle, r'SOFTWARE\lib_registry_test')
    """
    _check_key(key)
    _check_argument_must_be_str_or_none(arg_number=2, argument=sub_key)

    key_handle = _resolve_key(key)
    key_handle = OpenKey(key_handle, sub_key)
    try:
        fval = _get_backend().get_value(key_handle.handle, "")
        if not isinstance(fval.value, str):
            os_error = OSError("[WinError 13] The data is invalid")
            os_error.winerror = 13  # type: ignore[attr-defined]
            raise os_error
        return fval.value
    except (KeyError, FileNotFoundError):
        return ""


def QueryValueEx(key: Handle, value_name: str | None, /) -> tuple[RegData, int]:
    r"""Retrieve value data and type for a named value.

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, 18446744071562067970)
    >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion')
    >>> QueryValueEx(key_handle, 'CurrentBuild')
    ('...', 1)
    """
    _check_key(key)
    _check_argument_must_be_str_or_none(arg_number=2, argument=value_name)

    if value_name is None:
        value_name = ""
    key_handle = _resolve_key(key)
    fval = _get_backend().get_value(key_handle.handle, value_name)
    return fval.value, fval.value_type


def SetValue(key: Handle, sub_key: str | None, type: int, value: str, /) -> None:
    r"""Set the default value of a key (REG_SZ only).

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, 18446744071562067969)
    >>> key_handle = CreateKey(reg_handle, r'SOFTWARE\lib_registry_test')
    >>> SetValue(key_handle, '', 1, 'test1')
    >>> assert QueryValue(reg_handle, r'SOFTWARE\lib_registry_test') == 'test1'
    >>> DeleteKey(reg_handle, r'SOFTWARE\lib_registry_test')
    """
    _check_key(key)
    _check_argument_must_be_str_or_none(arg_number=2, argument=sub_key)
    _check_argument_must_be_type_expected(arg_number=3, argument=type, type_expected=int)
    _check_argument_must_be_type_expected(arg_number=4, argument=value, type_expected=str)

    if type != REG_SZ:
        raise TypeError("type must be winreg.REG_SZ")

    key_handle = _resolve_key(key)
    access = key_handle._access  # type: ignore[reportPrivateUsage]
    try:
        key_handle = OpenKey(key_handle, sub_key, 0, access=access)
    except FileNotFoundError:
        key_handle = CreateKey(key_handle, sub_key)
    SetValueEx(key_handle, "", 0, REG_SZ, value)


def SetValueEx(
    key: Handle,
    value_name: str | None,
    reserved: int,
    type: int,
    value: RegData,
    /,
) -> None:
    r"""Store data in a named value of an open registry key.

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, 18446744071562067969)
    >>> key_handle = CreateKey(reg_handle, r'Software\lib_registry_test')
    >>> SetValueEx(key_handle, 'some_test', 0, 1, 'some_test_value')
    >>> assert QueryValueEx(key_handle, 'some_test') == ('some_test_value', 1)
    >>> DeleteValue(key_handle, 'some_test')
    >>> DeleteKey(key_handle, '')
    """
    _check_key(key)
    _check_argument_must_be_str_or_none(arg_number=2, argument=value_name)
    _check_argument_must_be_type_expected(arg_number=4, argument=type, type_expected=int)

    if value_name is None:
        value_name = ""
    check_value_type_matches_type(value, type)
    key_handle = _resolve_key(key)
    _get_backend().set_value(key_handle.handle, value_name, value, type)


def DisableReflectionKey(key: Handle, /) -> None:
    """Disable registry reflection for 32-bit processes on 64-bit systems.

    No-op in fake implementation — reflection is not simulated.

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg = ConnectRegistry(None, 18446744071562067970)
    >>> DisableReflectionKey(reg)
    """


def EnableReflectionKey(key: Handle, /) -> None:
    """Re-enable registry reflection for 32-bit processes on 64-bit systems.

    No-op in fake implementation — reflection is not simulated.

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg = ConnectRegistry(None, 18446744071562067970)
    >>> EnableReflectionKey(reg)
    """


def QueryReflectionKey(key: Handle, /) -> bool:
    """Check whether registry reflection is disabled for a key.

    Always returns ``True`` (reflection enabled) in fake implementation.

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg = ConnectRegistry(None, 18446744071562067970)
    >>> QueryReflectionKey(reg)
    True
    """
    return True


def FlushKey(key: Handle, /) -> None:
    """Write all attributes of a key to the registry.

    No-op in fake implementation — data is already in memory.

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg = ConnectRegistry(None, 18446744071562067970)
    >>> FlushKey(reg)
    """
    _check_key(key)


def ExpandEnvironmentStrings(string: str, /) -> str:
    r"""Expand ``%VAR%``-style environment-variable references in a string.

    Handles the Windows ``%VAR%`` syntax on all platforms.

    >>> ExpandEnvironmentStrings('unchanged')
    'unchanged'
    """

    def _replace(match: re.Match[str]) -> str:
        return os.environ.get(match.group(1), match.group(0))

    return _RE_PERCENT_VAR.sub(_replace, string)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _resolve_key(key: Handle) -> PyHKEY:
    """Convert any Handle form (int, HKEYType, PyHKEY) to PyHKEY."""
    if isinstance(key, PyHKEY):
        return key
    elif isinstance(key, int):
        hive_key = _get_backend().get_hive(key)
        return PyHKEY(hive_key)
    elif isinstance(key, HKEYType):  # type: ignore[reportUnnecessaryIsInstance]
        return PyHKEY(handle=key.handle, access=key._access)  # type: ignore[reportPrivateUsage]
    else:
        raise RuntimeError("unknown Key Type")


__all__ = [
    "CloseKey",
    "ConnectRegistry",
    "CreateKey",
    "CreateKeyEx",
    "DeleteKey",
    "DeleteKeyEx",
    "DeleteValue",
    "DisableReflectionKey",
    "EnableReflectionKey",
    "EnumKey",
    "EnumValue",
    "ExpandEnvironmentStrings",
    "FlushKey",
    "OpenKey",
    "OpenKeyEx",
    "QueryInfoKey",
    "QueryReflectionKey",
    "QueryValue",
    "QueryValueEx",
    "SetValue",
    "SetValueEx",
    "configure_network_resolver",
    "error",
    "load_fake_registry",
    "use_backend",
]
