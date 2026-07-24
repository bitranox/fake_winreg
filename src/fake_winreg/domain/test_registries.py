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
        sub_key=r"SOFTWARE\Microsoft\Windows NT\CurrentVersion",
        value_name="CurrentBuild",
        value="18363",
    )

    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        sub_key=r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\S-1-5-18",
        value_name="ProfileImagePath",
        value=r"%systemroot%\system32\config\systemprofile",
        value_type=REG_EXPAND_SZ,
    )
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        sub_key=r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\S-1-5-19",
        value_name="ProfileImagePath",
        value=r"%systemroot%\ServiceProfiles\LocalService",
        value_type=REG_EXPAND_SZ,
    )
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        sub_key=r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\S-1-5-20",
        value_name="ProfileImagePath",
        value=r"%systemroot%\ServiceProfiles\NetworkService",
        value_type=REG_EXPAND_SZ,
    )
    sid = "S-1-5-21-206651429-2786145735-121611483-1001"
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        sub_key=rf"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\{sid}",
        value_name="ProfileImagePath",
        value=r"C:\Users\bitranox",
        value_type=REG_EXPAND_SZ,
    )

    set_fake_reg_key(fake_registry.hive[HKEY_USERS], ".DEFAULT")
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], "S-1-5-18")
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], "S-1-5-19")
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], "S-1-5-20")
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], sid)
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], f"{sid}_Classes")
    set_fake_reg_value(
        fake_registry.hive[HKEY_USERS],
        sub_key=f"{sid}\\Volatile Environment",
        value_name="USERNAME",
        value="bitranox",
        value_type=REG_SZ,
    )

    return fake_registry


def get_minimal_windows11_testregistry(fake_registry: FakeRegistry | None = None) -> FakeRegistry:
    r"""Build a minimal Windows 11 23H2 Pro registry for testing.

    Windows 11 is detected by ``CurrentBuild >= 22000``.  The ``ProductName``
    value still reads ``"Windows 10 Pro"`` in the registry - Microsoft never
    updated it.  Software must check ``CurrentBuild`` or ``DisplayVersion``
    to distinguish Windows 11 from Windows 10.

    >>> fake_registry = get_minimal_windows11_testregistry()
    >>> fake_reg = FakeRegistry()
    >>> fake_registry2 = get_minimal_windows11_testregistry(fake_reg)
    """
    if fake_registry is None:
        fake_registry = FakeRegistry()

    cv = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"

    # Core version values - ProductName intentionally says "Windows 10"
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE], sub_key=cv, value_name="ProductName", value="Windows 10 Pro"
    )
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], sub_key=cv, value_name="DisplayVersion", value="23H2")
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], sub_key=cv, value_name="CurrentBuild", value="22631")
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE], sub_key=cv, value_name="CurrentBuildNumber", value="22631"
    )
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], sub_key=cv, value_name="CurrentVersion", value="6.3")
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        sub_key=cv,
        value_name="CurrentMajorVersionNumber",
        value=10,
        value_type=REG_DWORD,
    )
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        sub_key=cv,
        value_name="CurrentMinorVersionNumber",
        value=0,
        value_type=REG_DWORD,
    )
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE], sub_key=cv, value_name="UBR", value=4317, value_type=REG_DWORD
    )  # KB5044285, Oct 2024
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], sub_key=cv, value_name="EditionID", value="Professional")
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE], sub_key=cv, value_name="InstallationType", value="Client"
    )
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], sub_key=cv, value_name="BuildBranch", value="ni_release")
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE], sub_key=cv, value_name="BuildLab", value="22621.ni_release.220506-1250"
    )
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        sub_key=cv,
        value_name="BuildLabEx",
        value="22621.1.amd64fre.ni_release.220506-1250",
    )

    # System profiles
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        sub_key=cv + r"\ProfileList\S-1-5-18",
        value_name="ProfileImagePath",
        value=r"%systemroot%\system32\config\systemprofile",
        value_type=REG_EXPAND_SZ,
    )
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        sub_key=cv + r"\ProfileList\S-1-5-19",
        value_name="ProfileImagePath",
        value=r"%systemroot%\ServiceProfiles\LocalService",
        value_type=REG_EXPAND_SZ,
    )
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        sub_key=cv + r"\ProfileList\S-1-5-20",
        value_name="ProfileImagePath",
        value=r"%systemroot%\ServiceProfiles\NetworkService",
        value_type=REG_EXPAND_SZ,
    )
    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        sub_key=cv + r"\ProfileList\S-1-5-21-3623811015-3361044348-30300820-1013",
        value_name="ProfileImagePath",
        value=r"C:\Users\TestUser",
        value_type=REG_EXPAND_SZ,
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
        sub_key=r"S-1-5-21-3623811015-3361044348-30300820-1013\Volatile Environment",
        value_name="USERNAME",
        value="TestUser",
        value_type=REG_SZ,
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
        sub_key=r"Software\Microsoft\Windows NT\CurrentVersion",
        value_name="CurrentBuild",
        value="7601",
    )

    set_fake_reg_value(
        fake_registry.hive[HKEY_LOCAL_MACHINE],
        sub_key=r"Software\Microsoft\Windows NT\CurrentVersion\ProfileList\S-1-5-21-0-0-0-1000",
        value_name="ProfileImagePath",
        value=r"C:\users\bitranox",
        value_type=REG_EXPAND_SZ,
    )

    set_fake_reg_key(fake_registry.hive[HKEY_USERS], r".Default")
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], r"S-1-5-21-0-0-0-1000")
    set_fake_reg_value(
        fake_registry.hive[HKEY_USERS],
        sub_key=r"S-1-5-21-0-0-0-1000\Volatile Environment",
        value_name="USERNAME",
        value="bitranox",
        value_type=REG_SZ,
    )

    return fake_registry


__all__ = [
    "get_minimal_windows11_testregistry",
    "get_minimal_windows_testregistry",
    "get_minimal_wine_testregistry",
]
