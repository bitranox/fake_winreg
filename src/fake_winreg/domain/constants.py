"""Windows Registry constants for hive keys, value types, and access rights."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Predefined HKEY root constants
# ---------------------------------------------------------------------------
HKEY_CLASSES_ROOT: int = 18446744071562067968
HKEY_CURRENT_CONFIG: int = 18446744071562067973
HKEY_CURRENT_USER: int = 18446744071562067969
HKEY_DYN_DATA: int = 18446744071562067974
HKEY_LOCAL_MACHINE: int = 18446744071562067970
HKEY_PERFORMANCE_DATA: int = 18446744071562067972
HKEY_USERS: int = 18446744071562067971

# ---------------------------------------------------------------------------
# Registry value types (REG_*)
# ---------------------------------------------------------------------------
REG_NONE: int = 0
REG_SZ: int = 1
REG_EXPAND_SZ: int = 2
REG_BINARY: int = 3
REG_DWORD: int = 4
REG_DWORD_LITTLE_ENDIAN: int = 4
REG_DWORD_BIG_ENDIAN: int = 5
REG_LINK: int = 6
REG_MULTI_SZ: int = 7
REG_RESOURCE_LIST: int = 8
REG_FULL_RESOURCE_DESCRIPTOR: int = 9
REG_RESOURCE_REQUIREMENTS_LIST: int = 10
REG_QWORD: int = 11
REG_QWORD_LITTLE_ENDIAN: int = 11

# ---------------------------------------------------------------------------
# Registry option constants
# ---------------------------------------------------------------------------
REG_OPTION_RESERVED: int = 0
REG_OPTION_NON_VOLATILE: int = 0
REG_OPTION_VOLATILE: int = 1
REG_OPTION_CREATE_LINK: int = 2
REG_OPTION_BACKUP_RESTORE: int = 4
REG_OPTION_OPEN_LINK: int = 8
REG_LEGAL_OPTION: int = 31
REG_CREATED_NEW_KEY: int = 1
REG_OPENED_EXISTING_KEY: int = 2
REG_WHOLE_HIVE_VOLATILE: int = 1
REG_REFRESH_HIVE: int = 2
REG_NO_LAZY_FLUSH: int = 4
REG_NOTIFY_CHANGE_ATTRIBUTES: int = 2
REG_NOTIFY_CHANGE_NAME: int = 1
REG_NOTIFY_CHANGE_LAST_SET: int = 4
REG_NOTIFY_CHANGE_SECURITY: int = 8
REG_LEGAL_CHANGE_FILTER: int = 268435471

# The type of a fake registry key in the csv file
REG_FAKE_KEY: int = -1

# ---------------------------------------------------------------------------
# Key access rights (KEY_*)
# ---------------------------------------------------------------------------
KEY_ALL_ACCESS: int = 983103
KEY_WRITE: int = 131078
KEY_READ: int = 131097
KEY_EXECUTE: int = 131097
KEY_QUERY_VALUE: int = 1
KEY_SET_VALUE: int = 2
KEY_CREATE_SUB_KEY: int = 4
KEY_ENUMERATE_SUB_KEYS: int = 8
KEY_NOTIFY: int = 16
KEY_CREATE_LINK: int = 32
KEY_WOW64_64KEY: int = 256
KEY_WOW64_32KEY: int = 512

# ---------------------------------------------------------------------------
# Hive name lookup by integer constant
# ---------------------------------------------------------------------------
hive_name_hashed_by_int: dict[int, str] = {
    18446744071562067968: "HKEY_CLASSES_ROOT",
    18446744071562067973: "HKEY_CURRENT_CONFIG",
    18446744071562067969: "HKEY_CURRENT_USER",
    18446744071562067974: "HKEY_DYN_DATA",
    18446744071562067970: "HKEY_LOCAL_MACHINE",
    18446744071562067972: "HKEY_PERFORMANCE_DATA",
    18446744071562067971: "HKEY_USERS",
}

__all__ = [
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
