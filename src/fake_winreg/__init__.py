"""Fake winreg — drop-in replacement for the Windows ``winreg`` module.

Provides a fake Windows registry for testing registry-dependent code on Linux.
Usage::

    import fake_winreg as winreg

    fake_registry = winreg.fake_reg_tools.get_minimal_windows_testregistry()
    winreg.load_fake_registry(fake_registry)

    reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    key_handle = winreg.OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')

Also re-exports scaffold infrastructure (configuration, metadata).
"""

from __future__ import annotations

# Metadata
from .__init__conf__ import print_info

# Persistence backends and IO
from .adapters.persistence import (
    JsonBackend,
    SqliteBackend,
    export_json,
    export_reg,
    import_json,
    import_reg,
)

# Composition exports (wired adapters) — also triggers network resolver wiring
from .composition import get_config

# Backward-compatible module aliases
from .domain import registry as fake_reg
from .domain import test_registries as fake_reg_tools

# API functions
from .domain.api import (
    CloseKey,
    ConnectRegistry,
    CreateKey,
    CreateKeyEx,
    DeleteKey,
    DeleteKeyEx,
    DeleteValue,
    DisableReflectionKey,
    EnableReflectionKey,
    EnumKey,
    EnumValue,
    ExpandEnvironmentStrings,
    FlushKey,
    OpenKey,
    OpenKeyEx,
    QueryInfoKey,
    QueryReflectionKey,
    QueryValue,
    QueryValueEx,
    SetValue,
    SetValueEx,
    error,
    load_fake_registry,
    use_backend,
)

# Constants
from .domain.constants import (
    HKEY_CLASSES_ROOT,
    HKEY_CURRENT_CONFIG,
    HKEY_CURRENT_USER,
    HKEY_DYN_DATA,
    HKEY_LOCAL_MACHINE,
    HKEY_PERFORMANCE_DATA,
    HKEY_USERS,
    KEY_ALL_ACCESS,
    KEY_CREATE_LINK,
    KEY_CREATE_SUB_KEY,
    KEY_ENUMERATE_SUB_KEYS,
    KEY_EXECUTE,
    KEY_NOTIFY,
    KEY_QUERY_VALUE,
    KEY_READ,
    KEY_SET_VALUE,
    KEY_WOW64_32KEY,
    KEY_WOW64_64KEY,
    KEY_WRITE,
    REG_BINARY,
    REG_CREATED_NEW_KEY,
    REG_DWORD,
    REG_DWORD_BIG_ENDIAN,
    REG_DWORD_LITTLE_ENDIAN,
    REG_EXPAND_SZ,
    REG_FAKE_KEY,
    REG_FULL_RESOURCE_DESCRIPTOR,
    REG_LEGAL_CHANGE_FILTER,
    REG_LEGAL_OPTION,
    REG_LINK,
    REG_MULTI_SZ,
    REG_NO_LAZY_FLUSH,
    REG_NONE,
    REG_NOTIFY_CHANGE_ATTRIBUTES,
    REG_NOTIFY_CHANGE_LAST_SET,
    REG_NOTIFY_CHANGE_NAME,
    REG_NOTIFY_CHANGE_SECURITY,
    REG_OPENED_EXISTING_KEY,
    REG_OPTION_BACKUP_RESTORE,
    REG_OPTION_CREATE_LINK,
    REG_OPTION_NON_VOLATILE,
    REG_OPTION_OPEN_LINK,
    REG_OPTION_RESERVED,
    REG_OPTION_VOLATILE,
    REG_QWORD,
    REG_QWORD_LITTLE_ENDIAN,
    REG_REFRESH_HIVE,
    REG_RESOURCE_LIST,
    REG_RESOURCE_REQUIREMENTS_LIST,
    REG_SZ,
    REG_WHOLE_HIVE_VOLATILE,
    hive_name_hashed_by_int,
)

# Handle types
from .domain.handles import Handle, HKEYType, PyHKEY
from .domain.memory_backend import InMemoryBackend

# Registry data structures
from .domain.registry import (
    FakeRegistry,
    FakeRegistryKey,
    FakeRegistryValue,
    get_fake_reg_key,
    get_windows_timestamp_now,
    set_fake_reg_key,
    set_fake_reg_value,
)

# ---------------------------------------------------------------------------
# Winreg-compatible public API
# ---------------------------------------------------------------------------
# Types
from .domain.types import RegData

__all__ = [
    # Metadata
    "print_info",
    "get_config",
    # Types
    "RegData",
    "Handle",
    "HKEYType",
    "PyHKEY",
    # Registry data structures
    "FakeRegistry",
    "FakeRegistryKey",
    "FakeRegistryValue",
    "get_fake_reg_key",
    "get_windows_timestamp_now",
    "set_fake_reg_key",
    "set_fake_reg_value",
    # API functions
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
    "error",
    "load_fake_registry",
    "use_backend",
    "InMemoryBackend",
    "JsonBackend",
    "SqliteBackend",
    "export_json",
    "export_reg",
    "import_json",
    "import_reg",
    # Module aliases
    "fake_reg",
    "fake_reg_tools",
    "HKEY_CLASSES_ROOT",
    "HKEY_CURRENT_CONFIG",
    "HKEY_CURRENT_USER",
    "HKEY_DYN_DATA",
    "HKEY_LOCAL_MACHINE",
    "HKEY_PERFORMANCE_DATA",
    "HKEY_USERS",
    "KEY_ALL_ACCESS",
    "KEY_CREATE_LINK",
    "KEY_CREATE_SUB_KEY",
    "KEY_ENUMERATE_SUB_KEYS",
    "KEY_EXECUTE",
    "KEY_NOTIFY",
    "KEY_QUERY_VALUE",
    "KEY_READ",
    "KEY_SET_VALUE",
    "KEY_WOW64_32KEY",
    "KEY_WOW64_64KEY",
    "KEY_WRITE",
    "REG_BINARY",
    "REG_CREATED_NEW_KEY",
    "REG_DWORD",
    "REG_DWORD_BIG_ENDIAN",
    "REG_DWORD_LITTLE_ENDIAN",
    "REG_EXPAND_SZ",
    "REG_FAKE_KEY",
    "REG_FULL_RESOURCE_DESCRIPTOR",
    "REG_LEGAL_CHANGE_FILTER",
    "REG_LEGAL_OPTION",
    "REG_LINK",
    "REG_MULTI_SZ",
    "REG_NO_LAZY_FLUSH",
    "REG_NONE",
    "REG_NOTIFY_CHANGE_ATTRIBUTES",
    "REG_NOTIFY_CHANGE_LAST_SET",
    "REG_NOTIFY_CHANGE_NAME",
    "REG_NOTIFY_CHANGE_SECURITY",
    "REG_OPENED_EXISTING_KEY",
    "REG_OPTION_BACKUP_RESTORE",
    "REG_OPTION_CREATE_LINK",
    "REG_OPTION_NON_VOLATILE",
    "REG_OPTION_OPEN_LINK",
    "REG_OPTION_RESERVED",
    "REG_OPTION_VOLATILE",
    "REG_QWORD",
    "REG_QWORD_LITTLE_ENDIAN",
    "REG_REFRESH_HIVE",
    "REG_RESOURCE_LIST",
    "REG_RESOURCE_REQUIREMENTS_LIST",
    "REG_SZ",
    "REG_WHOLE_HIVE_VOLATILE",
    "hive_name_hashed_by_int",
]
