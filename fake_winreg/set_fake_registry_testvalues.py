# PROJ
try:
    from .fake_registry import *
except (ImportError, ModuleNotFoundError):      # pragma: no cover
    # import for doctest
    from fake_registry import *                 # type: ignore  # pragma: no cover


def set_fake_test_registry_windows() -> FakeRegistry:
    """
    >>> fake_registry = set_fake_test_registry_windows()

    """
    fake_registry = FakeRegistry()

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


def set_fake_test_registry_wine() -> FakeRegistry:
    """
    >>> fake_registry = set_fake_test_registry_wine()

    """

    fake_registry = FakeRegistry()

    # Software Key for Wine
    set_fake_reg_key(fake_registry.hive[HKEY_LOCAL_MACHINE], r'Software\Wine')

    # Current Build
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], r'Software\Microsoft\Windows NT\CurrentVersion', 'CurrentBuild', '7601')

    # Profile List in Wine
    set_fake_reg_value(fake_registry.hive[HKEY_LOCAL_MACHINE], r'Software\Microsoft\Windows NT\CurrentVersion\ProfileList\S-1-5-21-0-0-0-1000',
                       'ProfileImagePath', r'C:\users\bitranox', REG_EXPAND_SZ)

    # User SIDs in Wine
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], r'.Default')
    set_fake_reg_key(fake_registry.hive[HKEY_USERS], r'S-1-5-21-0-0-0-1000')
    set_fake_reg_value(fake_registry.hive[HKEY_USERS], r'S-1-5-21-0-0-0-1000\Volatile Environment', 'USERNAME', 'bitranox', REG_SZ)

    return fake_registry
