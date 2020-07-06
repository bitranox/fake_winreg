# STDLIB
import pathlib
import platform
from typing import Any, List, Dict, Tuple, Union

# EXT
from docopt import docopt                               # type: ignore
is_platform_windows = platform.system().lower() == 'windows'

# Own
if is_platform_windows:
    import winreg                                       # type: ignore
else:
    import lib_fake_registry
    # an empty Registry at the Moment
    fake_registry = lib_fake_registry.FakeRegistry()
    winreg = lib_fake_registry.FakeWinReg(fake_registry)

# PROJ
try:
    from .__doc__ import __doc__
    from . import __init__conf__
except ImportError:                 # pragma: no cover
    # imports for doctest
    from __doc__ import __doc__     # type: ignore  # pragma: no cover
    import __init__conf__           # type: ignore  # pragma: no cover


main_key_hashed_by_name = {'hkey_classes_root': winreg.HKEY_CLASSES_ROOT,
                           'hkcr': winreg.HKEY_CLASSES_ROOT,
                           'hkey_current_config': winreg.HKEY_CURRENT_CONFIG,
                           'hkcc': winreg.HKEY_CURRENT_CONFIG,
                           'hkey_current_user': winreg.HKEY_CURRENT_USER,
                           'hkcu': winreg.HKEY_CURRENT_USER,
                           'hkey_dyn_data': winreg.HKEY_DYN_DATA,
                           'hkdd': winreg.HKEY_DYN_DATA,
                           'hkey_local_machine': winreg.HKEY_LOCAL_MACHINE,
                           'hklm': winreg.HKEY_LOCAL_MACHINE,
                           'hkey_performance_data': winreg.HKEY_PERFORMANCE_DATA,
                           'hkpd': winreg.HKEY_PERFORMANCE_DATA,
                           'hkey_users': winreg.HKEY_USERS,
                           'hku': winreg.HKEY_USERS
                           }                                            # type: Dict[str, Any]


l_hive_names = ['HKEY_LOCAL_MACHINE', 'HKLM', 'HKEY_CURRENT_USER', 'HKCU', 'HKEY_CLASSES_ROOT',
                'HKCR', 'HKEY_CURRENT_CONFIG', 'HKCC', 'HKEY_DYN_DATA', 'HKDD', 'HKEY_USERS',
                'HKU', 'HKEY_PERFORMANCE_DATA', 'HKPD'
                ]

hive_names_hashed_by_int = {winreg.HKEY_CLASSES_ROOT: 'HKEY_CLASSES_ROOT',
                            winreg.HKEY_CURRENT_CONFIG: 'HKEY_CURRENT_CONFIG',
                            winreg.HKEY_CURRENT_USER: 'HKEY_CURRENT_USER',
                            winreg.HKEY_DYN_DATA: 'HKEY_DYN_DATA',
                            winreg.HKEY_LOCAL_MACHINE: 'HKEY_LOCAL_MACHINE',
                            winreg.HKEY_PERFORMANCE_DATA: 'HKEY_PERFORMANCE_DATA',
                            winreg.HKEY_USERS: 'HKEY_USERS'}


class RegistryError(Exception):
    pass


class RegistryConnectionError(RegistryError):
    pass


class RegistryKeyError(RegistryError):
    pass


class RegistryHKeyError(RegistryKeyError):
    pass


class RegistryKeyNotFoundError(RegistryKeyError):
    pass


class RegistryKeyExistsError(RegistryKeyError):
    pass


def reg_connect(key: Union[str, int], computer_name: Union[None, str] = None) -> winreg.HKEYType:
    """
    Gets the registry handle to the hive of the given key :
    get_registry_connection('\hklm\software\....') --> reg_handle to hklm
    get_registry_connection(winreg.HKEY_LOCAL_MACHINE) --> reg_handle to hklm

    >>> reg_connect('HKCR')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <...PyHKEY object at ...>
    >>> reg_connect('HKCC')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <...PyHKEY object at ...>
    >>> reg_connect('HKCU')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <...PyHKEY object at ...>
    >>> reg_connect('HKDD')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <...PyHKEY object at ...>
    >>> reg_connect('HKLM')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <...PyHKEY object at ...>
    >>> reg_connect('HKPD')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <...PyHKEY object at ...>
    >>> reg_connect('HKU')   # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <...PyHKEY object at ...>
    >>> reg_connect(winreg.HKEY_LOCAL_MACHINE)   # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <...PyHKEY object at ...>

    >>> sid='S-1-5-20'
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\{}'.format(sid)
    >>> reg_connect(key)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <...PyHKEY object at ...>
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\{}'.format(sid)
    >>> reg_connect(key)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <...PyHKEY object at ...>
    >>> key = r'HKEY_LOCAL_MACHINE/SOFTWARE/Microsoft/Windows NT/CurrentVersion/ProfileList/{}'.format(sid)
    >>> reg_connect(key)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <...PyHKEY object at ...>

    >>> reg_connect('SPAM') # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    lib_registry.RegistryHKeyError: invalid KEY: "SPAM"

    """
    if isinstance(key, str):
        key = get_hkey_int(key)

    reg_handle = winreg.ConnectRegistry(computer_name, key)
    return reg_handle


def create_key(key: Union[str, int, winreg.HKEYType], sub_key: str = '', exist_ok: bool = True, parents: bool = False) -> None:
    """
    >>> create_key(r'HKCU\\Software\\lib_registry_test')
    >>> delete_key(r'HKCU\\Software\\lib_registry_test')
    """
    if (not exist_ok) and key_exist(key, sub_key):
        key_string = get_key_as_string(key, sub_key)
        raise RegistryKeyExistsError('can not create key, it already exists: "{key_string}"'.format(key_string=key_string))

    hive_key, sub_key = get_key_components(key, sub_key)


    if parents:
        pass
    else:
        reg_handle = open_key(hive_key, access=winreg.KEY_WRITE)
        winreg.CreateKey(reg_handle, sub_key)


def get_number_of_subkeys(key: Union[str, int, winreg.HKEYType], sub_key: str = '') -> int:
    """
    param key : one of the winreg HKEY_* constants :
                HKEY_CLASSES_ROOT, HKEY_CURRENT_CONFIG, HKEY_CURRENT_USER, HKEY_DYN_DATA,
                HKEY_LOCAL_MACHINE, HKEY_PERFORMANCE_DATA, HKEY_USERS

    >>> assert get_number_of_subkeys(winreg.HKEY_USERS) > 0
    >>> assert get_number_of_subkeys('HKEY_USERS') > 0
    """
    reg_handle = open_key(key=key, sub_key=sub_key)
    number_of_subkeys, number_of_values, last_modified_win_timestamp = winreg.QueryInfoKey(reg_handle)
    return int(number_of_subkeys)


def get_number_of_values(key: Union[str, int, winreg.HKEYType], sub_key: str = '') -> int:
    """
    param key : one of the winreg HKEY_* constants :
                HKEY_CLASSES_ROOT, HKEY_CURRENT_CONFIG, HKEY_CURRENT_USER, HKEY_DYN_DATA,
                HKEY_LOCAL_MACHINE, HKEY_PERFORMANCE_DATA, HKEY_USERS

    >>> assert get_number_of_values(winreg.HKEY_LOCAL_MACHINE, sub_key=r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion') > 0
    >>> assert get_number_of_values(r'HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion') > 0
    """
    reg_handle = open_key(key=key, sub_key=sub_key)
    number_of_subkeys, number_of_values, last_modified_win_timestamp = winreg.QueryInfoKey(reg_handle)
    return int(number_of_values)


def get_ls_user_sids() -> List[str]:
    """
    >>> ls_user_sids = get_ls_user_sids()
    >>> assert len(ls_user_sids) > 1
    >>> assert ls_user_sids[0].lower() == '.default'
    >>> # Windows: ['.DEFAULT', 'S-1-5-18', 'S-1-5-19', 'S-1-5-20', ...]
    >>> # Wine: ['.Default', 'S-1-5-21-0-0-0-1000']

    """
    ls_user_sids = []
    n_sub_keys = get_number_of_subkeys(key=winreg.HKEY_USERS)
    for i in range(n_sub_keys):
        subkey = winreg.EnumKey(winreg.HKEY_USERS, i)
        ls_user_sids.append(subkey)
    return sorted(ls_user_sids)


def get_username_from_sid(sid: str) -> str:
    """
    >>> ls_user_sids = get_ls_user_sids()
    >>> assert len(ls_user_sids) > 1
    >>> username = get_username_from_sid(ls_user_sids[1])
    >>> assert len(username) > 1        # 'systemprofile' on windows, '<username>' on wine
    """
    if get_is_platform_windows_wine():
        username = _get_username_from_sid_wine(sid)
    else:
        username = _get_username_from_sid_windows(sid)
    return username


def _get_username_from_sid_windows(sid: str) -> str:
    """
    >>> _get_username_from_sid_windows('S-1-5-18')
    'systemprofile'
    >>> _get_username_from_sid_windows('unknown')  # +ELLIPSIS +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    FileNotFoundError: [WinError 2] The system cannot find the file specified

    """
    reg_handle = reg_connect('HKEY_LOCAL_MACHINE')
    reg_handle = winreg.OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\{}'.format(sid))
    value, value_type = winreg.QueryValueEx(reg_handle, 'ProfileImagePath')
    username = pathlib.PureWindowsPath(value).name
    return username


def _get_username_from_sid_wine(sid: str) -> str:
    """
    >>> _get_username_from_sid_wine('S-1-5-21-0-0-0-1000')
    'bitranox'
    """

    reg_handle = reg_connect('HKEY_USERS')
    reg_handle = winreg.OpenKey(reg_handle, r'{}\\Volatile Environment'.format(sid))
    username, value_type = winreg.QueryValueEx(reg_handle, 'USERNAME')
    return str(username)


def get_value(key_name: str, value_name: str) -> Any:
    """
    >>> ### key and subkey exist
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'
    >>> build_str = get_value(key, 'CurrentBuild')
    >>> assert int(build_str) > 1

    >>> ### slashes are NOT supported since there are keys with a slash in it !
    >>> key = 'HKEY_LOCAL_MACHINE/SOFTWARE/Microsoft/Windows NT/CurrentVersion'
    >>> build_str = get_value(key, 'CurrentBuild')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    ...
    OSError: key or subkey not found


    >>> ### key does not exist
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\DoesNotExist'
    >>> get_value(key, 'ProfileImagePath')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    ...
    OSError: key or subkey not found

    >>> ### subkey does not exist
    >>> sid = 'S-1-5-20'
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'
    >>> get_value(key, 'does_not_exist')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    ...
    OSError: key or subkey not found

    """
    try:
        reg_handle = reg_connect(key_name)
        key_without_hive = remove_hive_from_keypath_if_present(key_name)
        key = winreg.OpenKey(reg_handle, key_without_hive)
        reg_value, reg_type = winreg.QueryValueEx(key, value_name)
        return reg_value
    except Exception:
        raise OSError('key or subkey not found')  # FileNotFoundError does not exist in Python 2.7


def delete_key(key_name: str) -> None:
    root_key = get_hkey_int(key_name)
    reg_path = remove_hive_from_keypath_if_present(key_name)
    winreg.DeleteKey(root_key, reg_path)


def set_value(key_name: str, value_name: str, value: Any, value_type: int = winreg.REG_SZ) -> None:
    """
    value_type:
    REG_BINARY	                Binary data in any form.
    REG_DWORD	                A 32-bit number.
    REG_DWORD_LITTLE_ENDIAN	    A 32-bit number in little-endian format.
    REG_DWORD_BIG_ENDIAN	    A 32-bit number in big-endian format.
    REG_EXPAND_SZ	            Null-terminated string containing references to environment variables (%PATH%).
    REG_LINK	                A Unicode symbolic link.
    REG_MULTI_SZ	            A sequence of null-terminated strings, terminated by two null characters.
                                (Python handles this termination automatically.)
    REG_NONE	                No defined value type.
    REG_RESOURCE_LIST	        A device-driver resource list.
    REG_SZ	                    A null-terminated string.

    >>> create_key(r'HKCU\\Software\\lib_registry_test')
    >>> set_value(key_name=r'HKCU\\Software\\lib_registry_test', value_name='test_name', value='test_string', value_type=winreg.REG_SZ)
    >>> result = get_value(key_name=r'HKCU\\Software\\lib_registry_test', value_name='test_name')
    >>> assert result == 'test_string'
    >>> delete_value(key_name=r'HKCU\\Software\\lib_registry_test', value_name='test_name')
    >>> delete_key(r'HKCU\\Software\\lib_registry_test')

    """
    root_key = get_hkey_int(key_name)
    reg_path = remove_hive_from_keypath_if_present(key_name)
    registry_key = winreg.OpenKey(root_key, reg_path, 0, winreg.KEY_WRITE)
    winreg.SetValueEx(registry_key, value_name, 0, value_type, value)
    winreg.CloseKey(registry_key)


def delete_value(key_name: str, value_name: str) -> None:
    root_key = get_hkey_int(key_name)
    reg_path = remove_hive_from_keypath_if_present(key_name)
    registry_key = winreg.OpenKey(root_key, reg_path, 0, winreg.KEY_ALL_ACCESS)
    winreg.DeleteValue(registry_key, value_name)
    winreg.CloseKey(registry_key)


def get_hkey_int(key_name: str) -> int:
    """
    gets the root hive key from a key_name, containing short or long form, not case sensitive

    >>> assert get_hkey_int('HKLM/something') == winreg.HKEY_LOCAL_MACHINE
    >>> assert get_hkey_int('hklm/something') == winreg.HKEY_LOCAL_MACHINE
    >>> assert get_hkey_int('HKEY_LOCAL_MACHINE/something') == winreg.HKEY_LOCAL_MACHINE
    >>> assert get_hkey_int('hkey_local_machine/something') == winreg.HKEY_LOCAL_MACHINE
    >>> get_hkey_int('Something/else')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    ...
    lib_registry.RegistryHKeyError: invalid KEY: "Something"

    """
    key_name = strip_slashes(key_name)
    main_key_name = get_first_part_of_the_key(key_name)
    main_key_name_lower = main_key_name.lower()
    if main_key_name_lower in main_key_hashed_by_name:
        main_key = int(main_key_hashed_by_name[main_key_name_lower])
        return main_key
    else:
        raise RegistryHKeyError('invalid KEY: "{main_key_name}"'.format(main_key_name=main_key_name))


def strip_slashes(input_string: str) -> str:
    """
    >>> strip_slashes('//test\\\\')
    'test'
    """
    input_string = input_string.strip('/')
    input_string = input_string.strip('\\')
    return input_string


def get_first_part_of_the_key(key_name: str) -> str:
    """
    >>> get_first_part_of_the_key('')
    ''
    >>> get_first_part_of_the_key('something/')
    'something'

    """
    key_name = key_name.split('/', 1)[0]
    key_name = key_name.split('\\', 1)[0]
    return key_name


def remove_hive_from_keypath_if_present(key_name: str) -> str:
    """
    >>> sid='S-1-5-20'
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\{}'.format(sid)
    >>> remove_hive_from_keypath_if_present(key)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    'SOFTWARE\\\\Microsoft\\\\Windows NT\\\\CurrentVersion\\\\ProfileList\\\\S-1-5-20'
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\{}'.format(sid)
    >>> remove_hive_from_keypath_if_present(key)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    'SOFTWARE\\\\Microsoft\\\\Windows NT\\\\CurrentVersion\\\\ProfileList\\\\S-1-5-20'
    >>> key = r'HKEY_LOCAL_MACHINE/SOFTWARE/Microsoft/Windows NT/CurrentVersion/ProfileList/{}'.format(sid)
    >>> remove_hive_from_keypath_if_present(key)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    'SOFTWARE/Microsoft/Windows NT/CurrentVersion/ProfileList/S-1-5-20'
    """

    result = key_name
    for hive_name in l_hive_names:
        hive_name = strip_slashes(hive_name)
        if key_name.startswith(hive_name):
            result = strip_slashes(key_name[len(hive_name):])
            break
    return result


def key_exist(key: Union[str, int, winreg.HKEYType], sub_key: str = '') -> bool:
    """
    >>> key_exist(r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
    True
    >>> key_exist(r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\DoesNotExist')
    False

    """

    try:
        open_key(key=key, sub_key=sub_key)
        return True
    except FileNotFoundError:
        return False


def open_key(key: Union[str, int, winreg.HKEYType], sub_key: str = '', access: int = winreg.KEY_READ) -> winreg.HKEYType:
    """
    Opens a registry key and returns a reg_handle to it.

    Parameters :    key         can be either a predefined HKEY_* constant,
                                a string containing the root key,
                                or an already open key

                    sub_key     a string with the desired subkey relative to the key

                    access      access is an integer that specifies an access mask that
                                describes the desired security access for the key. Default is winreg.KEY_READ

    >>> reg_handle_hklm = open_key(winreg.HKEY_LOCAL_MACHINE)
    >>> reg_handle1 = open_key(winreg.HKEY_LOCAL_MACHINE, sub_key=r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
    >>> reg_handle2 = open_key(r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
    >>> reg_handle3 = open_key(reg_handle_hklm, sub_key=r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
    >>> reg_handle4 = open_key(reg_handle3)
    >>> assert reg_handle1.data == reg_handle2.data == reg_handle3.data == reg_handle4.data

    """

    hive_key, sub_key = get_key_components(key, sub_key)

    if not isinstance(key, winreg.HKEYType):
        reg_handle = winreg.ConnectRegistry(None, hive_key)  # must not use keyword args here, only positional args !
    else:
        reg_handle = key

    # if we have a subkey, or the access is not the default value, open a new handle
    # otherwise return the old handle to save some time
    if sub_key or (access != winreg.KEY_READ):
        reg_handle = winreg.OpenKey(reg_handle, sub_key, 0, access)
    return reg_handle


def get_key_components(key: Union[str, int, winreg.HKEYType], sub_key: str = '') -> Tuple[int, str]:
    """
    Returns hive_key and sub_key relative zu hive_key if the type if the key is int or str
    """
    hive_key = 0
    if isinstance(key, str):
        hive_key = get_hkey_int(key)
        key_without_hive = remove_hive_from_keypath_if_present(key)
        if sub_key:
            sub_key = r'\\'.join([key_without_hive, sub_key])
        else:
            sub_key = key_without_hive
    elif isinstance(key, int):
        hive_key = key
        if hive_key not in hive_names_hashed_by_int:
            raise RegistryHKeyError('invalid KEY: "{hive_key}"'.format(hive_key=hive_key))

    return hive_key, sub_key


def get_key_as_string(key: Union[str, int, winreg.HKEYType], sub_key: str = '') -> str:
    """
    >>> reg_handle_hklm = open_key(winreg.HKEY_LOCAL_MACHINE)
    >>> get_key_as_string(winreg.HKEY_LOCAL_MACHINE)
    'HKEY_LOCAL_MACHINE'
    >>> get_key_as_string(winreg.HKEY_LOCAL_MACHINE, sub_key=r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
    'HKEY_LOCAL_MACHINE\\\\SOFTWARE\\\\Microsoft\\\\Windows NT\\\\CurrentVersion\\\\ProfileList'
    >>> get_key_as_string(reg_handle_hklm, sub_key=r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
    'sub_key: SOFTWARE\\\\Microsoft\\\\Windows NT\\\\CurrentVersion\\\\ProfileList'
    >>> get_key_as_string(reg_handle_hklm)
    'the key can not be determined, since it was passed by a handle'

    """
    hive_key, sub_key = get_key_components(key, sub_key)
    if isinstance(key, winreg.HKEYType):
        if sub_key:
            key_as_string = 'sub_key: ' + sub_key
        else:
            key_as_string = 'the key can not be determined, since it was passed by a handle'
    else:
        key_as_string = strip_slashes(hive_names_hashed_by_int[hive_key] + '\\' + sub_key)
    return key_as_string


def get_is_platform_windows_wine() -> bool:
    """
    >>> result = get_is_platform_windows_wine()

    """

    _is_platform_windows_wine = key_exist(r'HKEY_LOCAL_MACHINE\Software\Wine')
    return _is_platform_windows_wine


# we might import this module and call main from another program and pass docopt args manually
def main(docopt_args: Dict[str, Union[bool, str]]) -> None:
    """
    >>> docopt_args = dict()
    >>> docopt_args['--version'] = True
    >>> docopt_args['--info'] = False
    >>> main(docopt_args)   # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    version: ...


    >>> docopt_args['--version'] = False
    >>> docopt_args['--info'] = True
    >>> main(docopt_args)   # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    information for ...

    >>> docopt_args['--version'] = False
    >>> docopt_args['--info'] = False
    >>> main(docopt_args)


    """
    if docopt_args['--version']:
        __init__conf__.print_version()
    elif docopt_args['--info']:
        __init__conf__.print_info()


# entry point via commandline
def main_commandline() -> None:
    """
    >>> main_commandline()  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    docopt.DocoptExit: ...

    """
    docopt_args = docopt(__doc__)
    main(docopt_args)       # pragma: no cover


# entry point if main
if __name__ == '__main__':
    main_commandline()
