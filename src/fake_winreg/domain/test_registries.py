"""Pre-built test registries mimicking Windows and Wine environments.

These are pure functions that create populated FakeRegistry instances
for use in tests and doctests.
"""

from __future__ import annotations

from .constants import (
    HKEY_LOCAL_MACHINE,
    HKEY_USERS,
    REG_DWORD,
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


def get_minimal_windows11_testregistry(fake_registry: FakeRegistry | None = None) -> FakeRegistry:
    r"""Build a minimal Windows 11 23H2 Pro registry for testing.

    Windows 11 is detected by ``CurrentBuild >= 22000``.  The ``ProductName``
    value still reads ``"Windows 10 Pro"`` in the registry — Microsoft never
    updated it.  Software must check ``CurrentBuild`` or ``DisplayVersion``
    to distinguish Windows 11 from Windows 10.

    >>> fake_registry = get_minimal_windows11_testregistry()
    >>> fake_reg = FakeRegistry()
    >>> fake_registry2 = get_minimal_windows11_testregistry(fake_reg)
    """
    if fake_registry is None:
        fake_registry = FakeRegistry()

    cv = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"

    # Core version values — ProductName intentionally says "Windows 10"
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], cv, "ProductName", "Windows 10 Pro")
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], cv, "DisplayVersion", "23H2")
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], cv, "CurrentBuild", "22631")
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], cv, "CurrentBuildNumber", "22631")
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], cv, "CurrentVersion", "6.3")
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], cv, "CurrentMajorVersionNumber", 10, REG_DWORD)
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], cv, "CurrentMinorVersionNumber", 0, REG_DWORD)
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], cv, "UBR", 4291, REG_DWORD)
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], cv, "EditionID", "Professional")
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], cv, "InstallationType", "Client")
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], cv, "BuildBranch", "ni_release")
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], cv, "BuildLab", "22621.ni_release.220506-1250")
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE], cv, "BuildLabEx", "22621.1.amd64fre.ni_release.220506-1250"
    )

    # System profiles
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        cv + r"\ProfileList\S-1-5-18",
        "ProfileImagePath",
        r"%systemroot%\system32\config\systemprofile",
        REG_EXPAND_SZ,
    )
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        cv + r"\ProfileList\S-1-5-19",
        "ProfileImagePath",
        r"%systemroot%\ServiceProfiles\LocalService",
        REG_EXPAND_SZ,
    )
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        cv + r"\ProfileList\S-1-5-20",
        "ProfileImagePath",
        r"%systemroot%\ServiceProfiles\NetworkService",
        REG_EXPAND_SZ,
    )
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        cv + r"\ProfileList\S-1-5-21-3623811015-3361044348-30300820-1013",
        "ProfileImagePath",
        r"C:\Users\TestUser",
        REG_EXPAND_SZ,
    )

    # User hives
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], ".DEFAULT")
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], "S-1-5-18")
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], "S-1-5-19")
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], "S-1-5-20")
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], "S-1-5-21-3623811015-3361044348-30300820-1013")
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], "S-1-5-21-3623811015-3361044348-30300820-1013_Classes")
    set_fake_reg_value(
        fake_registry.hive[HKEY_USERS],
        r"S-1-5-21-3623811015-3361044348-30300820-1013\Volatile Environment",
        "USERNAME",
        "TestUser",
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
    "get_minimal_windows11_testregistry",
    "get_minimal_windows_testregistry",
    "get_minimal_wine_testregistry",
]
