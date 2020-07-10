# STDLIB
from typing import Optional

# PROJ
try:
    from .fake_reg import *
except (ImportError, ModuleNotFoundError):      # pragma: no cover
    # import for doctest
    from fake_reg import *                 # type: ignore  # pragma: no cover


def get_minimal_windows_testregistry(fake_registry: Optional[FakeRegistry] = None) -> FakeRegistry:
    """
    >>> fake_registry = get_minimal_windows_testregistry()

    """
    if fake_registry is None:
        fake_registry = FakeRegistry()
        # for mypy checks to get rid of Optional[]
        assert fake_registry is not None

    # Current Build
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], r'SOFTWARE\Microsoft\Windows NT\CurrentVersion', 'CurrentBuild', '18363')

    # Profile List in Windows10
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\S-1-5-18',
                       'ProfileImagePath', r'%systemroot%\system32\config\systemprofile', REG_EXPAND_SZ)
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\S-1-5-19',
                       'ProfileImagePath', r'%systemroot%\ServiceProfiles\LocalService', REG_EXPAND_SZ)
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\S-1-5-20',
                       'ProfileImagePath', r'%systemroot%\ServiceProfiles\NetworkService', REG_EXPAND_SZ)
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE],
                       r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\S-1-5-21-206651429-2786145735-121611483-1001',
                       'ProfileImagePath', r'C:\Users\bitranox', REG_EXPAND_SZ)

    # User SIDs in Windows10
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], '.DEFAULT')
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], 'S-1-5-18')
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], 'S-1-5-19')
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], 'S-1-5-20')
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], 'S-1-5-21-206651429-2786145735-121611483-1001')
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], 'S-1-5-21-206651429-2786145735-121611483-1001_Classes')
    set_fake_reg_value(fake_registry.hive[HKEY_USERS], r'S-1-5-21-206651429-2786145735-121611483-1001\Volatile Environment', 'USERNAME', 'bitranox', REG_SZ)

    return fake_registry


def get_minimal_wine_testregistry(_fake_registry: Optional[FakeRegistry] = None) -> FakeRegistry:
    """
    >>> fake_registry = get_minimal_wine_testregistry()

    """
    if _fake_registry is None:
        _fake_registry = FakeRegistry()
        # for mypy checks to get rid of Optional[]
        assert _fake_registry is not None

    # Software Key for Wine
    set_fake_reg_key(_fake_registry.hive[HKEY_LOCAL_MACHINE], r'Software\Wine')

    # Current Build
    set_fake_reg_value(_fake_registry.hive[HKEY_LOCAL_MACHINE], r'Software\Microsoft\Windows NT\CurrentVersion', 'CurrentBuild', '7601')

    # Profile List in Wine
    set_fake_reg_value(_fake_registry.hive[HKEY_LOCAL_MACHINE], r'Software\Microsoft\Windows NT\CurrentVersion\ProfileList\S-1-5-21-0-0-0-1000',
                       'ProfileImagePath', r'C:\users\bitranox', REG_EXPAND_SZ)

    # User SIDs in Wine
    set_fake_reg_key(_fake_registry.hive[HKEY_USERS], r'.Default')
    set_fake_reg_key(_fake_registry.hive[HKEY_USERS], r'S-1-5-21-0-0-0-1000')
    set_fake_reg_value(_fake_registry.hive[HKEY_USERS], r'S-1-5-21-0-0-0-1000\Volatile Environment', 'USERNAME', 'bitranox', REG_SZ)

    return _fake_registry
