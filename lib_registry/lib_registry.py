# STDLIB
import platform
from typing import Any, List, Dict, Tuple, Union

# EXT
from docopt import docopt
is_platform_windows = platform.system().lower() == 'windows'

if is_platform_windows:
    import winreg               # type: ignore
else:
    try:
        from .fake_classes import WinRegFake
    except (ImportError, ModuleNotFoundError):
        # import for doctest
        from fake_classes import WinRegFake

    winreg = WinRegFake()

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


def get_number_of_subkeys(key: winreg.HKEYType) -> int:
    """
    param key : one of the winreg HKEY_* constants :
                HKEY_CLASSES_ROOT, HKEY_CURRENT_CONFIG, HKEY_CURRENT_USER, HKEY_DYN_DATA,
                HKEY_LOCAL_MACHINE, HKEY_PERFORMANCE_DATA, HKEY_USERS

    >>> result = get_number_of_subkeys(winreg.HKEY_USERS)
    >>> assert result > 1

    """
    number_of_subkeys, number_of_values, last_modified_win_timestamp = winreg.QueryInfoKey(key)
    return int(number_of_subkeys)


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
    reg = get_registry_connection('HKEY_LOCAL_MACHINE')
    key = winreg.OpenKey(reg, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\{}'.format(sid))
    val, value_type = winreg.QueryValueEx(key, 'ProfileImagePath')
    username = str(val.rsplit('\\', 1)[1])
    return username


def _get_username_from_sid_wine(sid: str) -> str:
    reg = get_registry_connection('HKEY_USERS')
    key = winreg.OpenKey(reg, r'{}\Volatile Environment'.format(sid))
    username, value_type = winreg.QueryValueEx(key, 'USERNAME')
    return str(username)


def get_value(key_name: str, value_name: str) -> Any:
    """
    >>> ### key and subkey exist
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'
    >>> build_str = get_value(key, 'CurrentBuild')
    >>> assert int(build_str) > 1

    >>> ### slashes are NOT supported
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
        reg = get_registry_connection(key_name)
        key_without_hive = get_reg_path(key_name)
        key = winreg.OpenKey(reg, key_without_hive)
        val_type = winreg.QueryValueEx(key, value_name)
        result = val_type[0]
        return result
    except Exception:
        raise OSError('key or subkey not found')  # FileNotFoundError does not exist in Python 2.7


def create_key(key_name: str) -> None:
    """
    >>> create_key(r'HKCU\\Software\\lib_registry_test')
    >>> delete_key(r'HKCU\\Software\\lib_registry_test')
    """
    root_key = get_root_key(key_name)
    reg_path = get_reg_path(key_name)
    winreg.CreateKey(root_key, reg_path)


def delete_key(key_name: str) -> None:
    root_key = get_root_key(key_name)
    reg_path = get_reg_path(key_name)
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
    root_key = get_root_key(key_name)
    reg_path = get_reg_path(key_name)
    registry_key = winreg.OpenKey(root_key, reg_path, 0, winreg.KEY_WRITE)
    winreg.SetValueEx(registry_key, value_name, 0, value_type, value)
    winreg.CloseKey(registry_key)


def delete_value(key_name: str, value_name: str) -> None:
    root_key = get_root_key(key_name)
    reg_path = get_reg_path(key_name)
    registry_key = winreg.OpenKey(root_key, reg_path, 0, winreg.KEY_ALL_ACCESS)
    winreg.DeleteValue(registry_key, value_name)
    winreg.CloseKey(registry_key)


def get_registry_connection(key_name: str) -> winreg.HKEYType:
    """
    >>> get_registry_connection('HKCR')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <PyHKEY object at ...>
    >>> get_registry_connection('HKCC')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <PyHKEY object at ...>
    >>> get_registry_connection('HKCU')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <PyHKEY object at ...>
    >>> get_registry_connection('HKDD')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <PyHKEY object at ...>
    >>> get_registry_connection('HKLM')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <PyHKEY object at ...>
    >>> get_registry_connection('HKPD')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <PyHKEY object at ...>
    >>> get_registry_connection('HKU')   # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <PyHKEY object at ...>

    >>> sid='S-1-5-20'
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\{}'.format(sid)
    >>> get_registry_connection(key)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <PyHKEY object at ...>
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\{}'.format(sid)
    >>> get_registry_connection(key)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <PyHKEY object at ...>
    >>> key = r'HKEY_LOCAL_MACHINE/SOFTWARE/Microsoft/Windows NT/CurrentVersion/ProfileList/{}'.format(sid)
    >>> get_registry_connection(key)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <PyHKEY object at ...>

    """

    main_key = get_root_key(key_name)
    reg = winreg.ConnectRegistry(None, main_key)
    return reg


def get_root_key(key_name: str) -> int:
    """
    >>> result = get_root_key('HKLM/something')
    >>> result > 1
    True

    >>> result = get_root_key('hklm/something')
    >>> result > 1
    True

    >>> get_root_key('something/else')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    ...
    ValueError: the registry key needs to start with a valid root key

    """
    key_name = strip_leading_and_trailing_slashes(key_name)
    main_key_name = get_first_part_of_the_key(key_name)
    main_key_name = main_key_name.lower()
    if main_key_name in main_key_hashed_by_name:
        main_key = int(main_key_hashed_by_name[main_key_name])
        return main_key
    else:
        raise ValueError('the registry key needs to start with a valid root key')


def strip_leading_and_trailing_slashes(input_string: str) -> str:
    """
    >>> strip_leading_and_trailing_slashes('//test\\\\')
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
    key_name = split_on_first_appearance(key_name, '/')
    key_name = split_on_first_appearance(key_name, '\\')
    return key_name


def split_on_first_appearance(input_string: str, separator: str) -> str:
    """
    >>> split_on_first_appearance('test','/')
    'test'
    >>> split_on_first_appearance('test/','/')
    'test'
    >>> split_on_first_appearance('test/something','/')
    'test'
    """
    result = input_string.split(separator, 1)[0]
    return result


def get_reg_path(key_name: str) -> str:
    """
    >>> sid='S-1-5-20'
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\{}'.format(sid)
    >>> get_reg_path(key)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    'SOFTWARE\\\\Microsoft\\\\Windows NT\\\\CurrentVersion\\\\ProfileList\\\\S-1-5-20'
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\{}'.format(sid)
    >>> get_reg_path(key)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    'SOFTWARE\\\\Microsoft\\\\Windows NT\\\\CurrentVersion\\\\ProfileList\\\\S-1-5-20'
    >>> key = r'HKEY_LOCAL_MACHINE/SOFTWARE/Microsoft/Windows NT/CurrentVersion/ProfileList/{}'.format(sid)
    >>> get_reg_path(key)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    'SOFTWARE/Microsoft/Windows NT/CurrentVersion/ProfileList/S-1-5-20'
    """

    result = key_name
    for hive_name in l_hive_names:
        if key_name.startswith(hive_name):
            result = remove_prefix_including_first_slash_or_backslash(key_name)
            break
    return result


def key_exist(key_name: str) -> bool:
    """
    >>> key_exist(r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
    True
    >>> key_exist(r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\DoesNotExist')
    False

    """
    reg = get_registry_connection(key_name)
    key_without_hive = get_reg_path(key_name)
    # noinspection PyBroadException
    try:
        winreg.OpenKey(reg, key_without_hive)
        return True
    except Exception:  # FileNotFoundError does not exist in Python 2.7
        return False


def remove_prefix_including_first_slash_or_backslash(input_str: str) -> str:
    """
    >>> remove_prefix_including_first_slash_or_backslash('test')
    'test'
    >>> remove_prefix_including_first_slash_or_backslash('test/')
    ''
    >>> remove_prefix_including_first_slash_or_backslash('/test/')
    'test/'

    >>> remove_prefix_including_first_slash_or_backslash('test\\\\')
    ''
    >>> remove_prefix_including_first_slash_or_backslash('test/test2/test3')
    'test2/test3'
    >>> remove_prefix_including_first_slash_or_backslash('test\\test3\\test4')
    'test\\test3\\test4'

    """
    result = input_str
    if '\\' in input_str:
        result = input_str.split('\\', 1)[1]
    elif '/' in input_str:
        result = input_str.split('/', 1)[1]
    return result


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
