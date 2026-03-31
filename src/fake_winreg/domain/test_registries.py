"""Pre-built test registries mimicking Windows and Wine environments.

These are pure functions that create populated FakeRegistry instances
for use in tests and doctests.
"""

from __future__ import annotations

from .constants import (
    HKEY_LOCAL_MACHINE,
    HKEY_USERS,
    REG_EXPAND_SZ,
    REG_SZ,
)
from .registry import (
    FakeRegistry,
    set_fake_reg_key,
    set_fake_reg_value,
)


def get_minimal_windows_testregistry(fake_registry: FakeRegistry | None = None) -> FakeRegistry:
    r"""Build a minimal Windows 10-like registry for testing.

    >>> fake_registry = get_minimal_windows_testregistry()
    >>> fake_reg = FakeRegistry()
    >>> fake_registry2 = get_minimal_windows_testregistry(fake_reg)
    """
    if fake_registry is None:
        fake_registry = FakeRegistry()

    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion",
        "CurrentBuild",
        "18363",
    )

    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\S-1-5-18",
        "ProfileImagePath",
        r"%systemroot%\system32\config\systemprofile",
        REG_EXPAND_SZ,
    )
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\S-1-5-19",
        "ProfileImagePath",
        r"%systemroot%\ServiceProfiles\LocalService",
        REG_EXPAND_SZ,
    )
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\S-1-5-20",
        "ProfileImagePath",
        r"%systemroot%\ServiceProfiles\NetworkService",
        REG_EXPAND_SZ,
    )
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\S-1-5-21-206651429-2786145735-121611483-1001",
        "ProfileImagePath",
        r"C:\Users\bitranox",
        REG_EXPAND_SZ,
    )

    set_fake_reg_key(fake_registry.hive[HKEY_USERS], ".DEFAULT")
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], "S-1-5-18")
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], "S-1-5-19")
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], "S-1-5-20")
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], "S-1-5-21-206651429-2786145735-121611483-1001")
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], "S-1-5-21-206651429-2786145735-121611483-1001_Classes")
    set_fake_reg_value(
        fake_registry.hive[HKEY_USERS],
        r"S-1-5-21-206651429-2786145735-121611483-1001\Volatile Environment",
        "USERNAME",
        "bitranox",
        REG_SZ,
    )

    return fake_registry


def get_minimal_wine_testregistry(fake_registry: FakeRegistry | None = None) -> FakeRegistry:
    r"""Build a minimal Wine-like registry for testing.

    >>> fake_registry = get_minimal_wine_testregistry()
    >>> fake_reg = FakeRegistry()
    >>> fake_registry2 = get_minimal_wine_testregistry(fake_reg)
    """
    if fake_registry is None:
        fake_registry = FakeRegistry()

    set_fake_reg_key(fake_registry.hive[HKEY_LOCAL_MACHINE], r"Software\Wine")

    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        r"Software\Microsoft\Windows NT\CurrentVersion",
        "CurrentBuild",
        "7601",
    )

    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        r"Software\Microsoft\Windows NT\CurrentVersion\ProfileList\S-1-5-21-0-0-0-1000",
        "ProfileImagePath",
        r"C:\users\bitranox",
        REG_EXPAND_SZ,
    )

    set_fake_reg_key(fake_registry.hive[HKEY_USERS], r".Default")
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], r"S-1-5-21-0-0-0-1000")
    set_fake_reg_value(
        fake_registry.hive[HKEY_USERS],
        r"S-1-5-21-0-0-0-1000\Volatile Environment",
        "USERNAME",
        "bitranox",
        REG_SZ,
    )

    return fake_registry


__all__ = [
    "get_minimal_windows_testregistry",
    "get_minimal_wine_testregistry",
]
