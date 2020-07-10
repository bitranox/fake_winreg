# CONSTANTS
HKEY_CLASSES_ROOT: int = 18446744071562067968
HKEY_CURRENT_CONFIG: int = 18446744071562067973
HKEY_CURRENT_USER: int = 18446744071562067969
HKEY_DYN_DATA: int = 18446744071562067974
HKEY_LOCAL_MACHINE: int = 18446744071562067970
HKEY_PERFORMANCE_DATA: int = 18446744071562067972
HKEY_USERS: int = 18446744071562067971

# value Types
REG_BINARY: int = 3                 # Binary data in any form.
REG_DWORD: int = 4                  # 32 - bit number.
REG_DWORD_LITTLE_ENDIAN: int = 4    # A 32 - bit number in little - endian format.Equivalent to REG_DWORD.
REG_DWORD_BIG_ENDIAN: int = 5       # A 32 - bit number in big - endian format.
REG_EXPAND_SZ: int = 2              # Null - terminated string containing references to environment variables( % PATH %).
REG_LINK: int = 6                   # A Unicode symbolic link.
REG_MULTI_SZ: int = 7               # A sequence of null - terminated strings, terminated by two null characters. python handles this termination automatically
REG_NONE: int = 0                   # No defined value type.
REG_QWORD: int = 11                 # A 64 - bit number.
REG_QWORD_LITTLE_ENDIAN: int = 11   # A 64 - bit number in little - endian format.Equivalent to REG_QWORD.
REG_RESOURCE_LIST: int = 8          # A device - driver resource list.
REG_FULL_RESOURCE_DESCRIPTOR: int = 9       # A hardware setting.
REG_RESOURCE_REQUIREMENTS_LIST: int = 10    # A hardware resource list.
REG_SZ: int = 1                             # A null-terminated string.
# the type of a fake registry key in the csv file
REG_FAKE_KEY = -1

# key access rights
# Combines the STANDARD_RIGHTS_REQUIRED, KEY_QUERY_VALUE, KEY_SET_VALUE, KEY_CREATE_SUB_KEY,
# KEY_ENUMERATE_SUB_KEYS, KEY_NOTIFY, and KEY_CREATE_LINK access rights.
KEY_ALL_ACCESS = 983103
KEY_WRITE = 131078          # Combines the STANDARD_RIGHTS_WRITE, KEY_SET_VALUE, and KEY_CREATE_SUB_KEY access rights.
KEY_READ = 131097           # Combines the STANDARD_RIGHTS_READ, KEY_QUERY_VALUE, KEY_ENUMERATE_SUB_KEYS, and KEY_NOTIFY values.
KEY_EXECUTE = 131097        # Equivalent to KEY_READ.
KEY_QUERY_VALUE = 1         # Required to query the values of a registry key.
KEY_SET_VALUE = 2           # Required to create, delete, or set a registry value.
KEY_CREATE_SUB_KEY = 4      # Required to create a subkey of a registry key.
KEY_ENUMERATE_SUB_KEYS = 8  # Required to enumerate the subkeys of a registry key.
KEY_NOTIFY = 16             # Required to request change notifications for a registry key or for subkeys of a registry key.
KEY_CREATE_LINK = 32        # Reserved for system use.
KEY_WOW64_64KEY = 256       # Indicates that an application on 64-bit Windows should operate on the 64-bit registry view.
KEY_WOW64_32KEY = 512       # Indicates that an application on 64-bit Windows should operate on the 32-bit registry view.


hive_name_hashed_by_int = dict()
hive_name_hashed_by_int[18446744071562067968] = 'HKEY_CLASSES_ROOT'
hive_name_hashed_by_int[18446744071562067973] = 'HKEY_CURRENT_CONFIG'
hive_name_hashed_by_int[18446744071562067969] = 'HKEY_CURRENT_USER'
hive_name_hashed_by_int[18446744071562067974] = 'HKEY_DYN_DATA'
hive_name_hashed_by_int[18446744071562067970] = 'HKEY_LOCAL_MACHINE'
hive_name_hashed_by_int[18446744071562067972] = 'HKEY_PERFORMANCE_DATA'
hive_name_hashed_by_int[18446744071562067971] = 'HKEY_USERS'
