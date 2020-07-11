# STDLIB
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, Union, cast, List


# EXT
import wrapt

# OWN
try:
    from .registry_constants import *
    from . import fake_reg
    from . import fake_reg_tools
except (ImportError, ModuleNotFoundError):                           # pragma: no cover
    # imports for doctest
    from registry_constants import *    # type: ignore  # pragma: no cover
    import fake_reg                     # type: ignore  # pragma: no cover
    import fake_reg_tools          # type: ignore  # pragma: no cover


F = TypeVar('F', bound=Callable[..., Any])


@wrapt.decorator
def check_for_kwargs_wrapt(wrapped: F, instance: object = None, args: Any = (), kwargs: Any = dict()) -> F:     # noqa
    if kwargs:                                            # pragma: no cover
        keys = ', '.join([key for key in kwargs.keys()])  # pragma: no cover
        raise TypeError("{fn}() got some positional-only arguments passed as keyword arguments: '{keys}'".format(
            fn=wrapped.__name__, keys=keys))              # pragma: no cover
    return cast(F, wrapped(*args, **kwargs))


@check_for_kwargs_wrapt
def test(x: int) -> None:
    """
    >>> test(x=5)
    Traceback (most recent call last):
        ...
    TypeError: test() got some positional-only arguments passed as keyword arguments: 'x'

    """
    print(x)


class PyHKEY(object):
    """
    Registry Handle Objects
    This object wraps a Windows HKEY object, automatically closing it when the object is destroyed.
    To guarantee cleanup, you can call either the Close() method on the object, or the CloseKey() function.
    All registry functions in this module return one of these objects.

    # Not implemented features of the Original Object - its not hard, but I did not need it ATM:
    All registry functions in this module which accept a handle object also accept an integer, however, use of the handle object is encouraged.
    Handle objects provide semantics for __bool__() – thus
    if handle:
        print("Yes")
    will print Yes if the handle is currently valid (has not been closed or detached).

    The object also support comparison semantics, so handle objects will compare true if they both reference the same underlying Windows handle value.
    Handle objects can be converted to an integer (e.g., using the built-in int() function), in which case the underlying Windows handle value is returned.
    You can also use the Detach() method to return the integer handle, and also disconnect the Windows handle from the handle object.

    >>> p = PyHKEY(fake_reg.FakeRegistryKey())
    >>> p.Close()
    >>> assert p.Detach() == 0

    """

    def __init__(self, data: fake_reg.FakeRegistryKey, access: int = KEY_READ):
        self.data = data
        self.access = access

    @staticmethod
    def Close() -> None:    # noqa
        """
        Closes the underlying Windows handle.
        If the handle is already closed, no error is raised.
        """
        pass

    @staticmethod
    def Detach() -> int:  # noqa
        """
        Detaches the Windows handle from the handle object.
        The result is an integer that holds the value of the handle before it is detached.
        If the handle is already detached or closed, this will return zero.
        After calling this function, the handle is effectively invalidated,
        but the handle is not closed.
        You would call this function when you need the underlying Win32 handle
        to exist beyond the lifetime of the handle object.
        Raises an auditing event winreg.PyHKEY.Detach with argument key.
        """
        return 0


HKEYType = PyHKEY

__fake_registry = fake_reg.FakeRegistry()
# the list of the open handles - hashed by full_key_path
__py_hive_handles: Dict[str, PyHKEY] = dict()


def load_fake_registry(fake_registry: fake_reg.FakeRegistry) -> None:
    global __fake_registry
    global __py_hive_handles
    __fake_registry = fake_registry
    __py_hive_handles = dict()


@check_for_kwargs_wrapt
def CloseKey(hkey: Union[int, PyHKEY]) -> None:      # noqa
    """
    Closes a previously opened registry key. The hkey argument specifies a previously opened hive key.

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> # Test
    >>> hive_key = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
    >>> CloseKey(HKEY_LOCAL_MACHINE)

    >>> # must not accept keyword parameters
    >>> hive_key = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
    >>> CloseKey(hkey=HKEY_LOCAL_MACHINE)
    Traceback (most recent call last):
        ...
    TypeError: CloseKey() got some positional-only arguments passed as keyword arguments: 'hkey'

    """
    # we could recursively delete all the handles in self.py_hkey_handles by walking the fake registry keys - atm we dont bother
    # or we can get the hive name and delete all self.py_hkey_handles beginning with hive name
    # the objects are destroyed anyway when we close fake_winreg object, so we dont bother
    pass


@check_for_kwargs_wrapt
def ConnectRegistry(computer_name: Union[None, str], key: int) -> PyHKEY:     # noqa
    """
    Establishes a connection to a predefined registry handle on another computer, and returns a handle object.
    computer_name : the name of the remote computer, of the form r"\\computername". If None, the local computer is used.  (NOT IMPLEMENTED)
    key: the predefined handle to connect to.
    The return value is the handle of the opened key. If the function fails, an OSError exception is raised.
    Raises an auditing event winreg.ConnectRegistry with arguments computer_name, key.


    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)

    >>> # Connect
    >>> ConnectRegistry(None, HKEY_LOCAL_MACHINE)
    <...PyHKEY object at ...>

    >>> # Computername given
    >>> ConnectRegistry('test', HKEY_LOCAL_MACHINE)
    Traceback (most recent call last):
    ...
    FileNotFoundError: System error 53 has occurred. The network path was not found

    >>> # Invalid Handle
    >>> ConnectRegistry(None, 42)
    Traceback (most recent call last):
        ...
    OSError: [WinError 6] The handle is invalid

    >>> # must not accept keyword parameters
    >>> ConnectRegistry(computer_name=None, key=HKEY_LOCAL_MACHINE)
    Traceback (most recent call last):
        ...
    TypeError: ConnectRegistry() got some positional-only arguments passed as keyword arguments: 'computer_name, key'

    >>> # Try to connect to computer
    >>> ConnectRegistry('HAL', HKEY_LOCAL_MACHINE)
    Traceback (most recent call last):
        ...
    FileNotFoundError: System error 53 has occurred. The network path was not found


    """
    if computer_name:
        network_error = FileNotFoundError('System error 53 has occurred. The network path was not found')
        setattr(network_error, 'winerror', 53)
        raise network_error
    try:
        fake_reg_handle = __fake_registry.hive[key]
    except KeyError:
        error = OSError('[WinError 6] The handle is invalid')
        setattr(error, 'winerror', 6)
        raise error

    hive_handle = PyHKEY(data=fake_reg_handle)
    hive_handle = __add_key_handle_to_hash_or_return_existing_handle(hive_handle)

    return hive_handle


@check_for_kwargs_wrapt
def CreateKey(key: Union[PyHKEY, int], sub_key: Union[str, None]) -> PyHKEY:      # noqa
    """
    Creates or opens the specified key, returning a handle object.
    key is an already open key, or one of the predefined HKEY_* constants.
    sub_key is a string that names the key this method opens or creates.
    If key is one of the predefined keys, sub_key may be None. In that case,
    the handle returned is the same key handle passed in to the function.
    If the key already exists, this function opens the existing key.
    The return value is the handle of the opened key. If the function fails, an OSError exception is raised.
    The sub_key can contain a directory structure like r'Software\\xxx\\yyy' - all the parents to yyy will be created

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)

    >>> # Connect
    >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)

    >>> # create key
    >>> key_handle_created = CreateKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')

    >>> # create an existing key - we get the same handle back
    >>> key_handle_existing = CreateKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
    >>> assert key_handle_existing == key_handle_created

    >>> # provoke Error on empty subkey
    >>> key_handle_existing = CreateKey(reg_handle, r'')
    Traceback (most recent call last):
        ...
    OSError: [WinError 1010] The configuration registry key is invalid.

    >>> # Teardown
    >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
    >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx')

    """
    if not sub_key:
        error = OSError('[WinError 1010] The configuration registry key is invalid.')
        setattr(error, 'winerror', 1010)
        raise error

    key_handle = __resolve_key(key)
    access = key_handle.access
    fake_reg_key = fake_reg.set_fake_reg_key(key_handle.data, sub_key=sub_key)
    key_handle = PyHKEY(fake_reg_key, access=access)
    key_handle = __add_key_handle_to_hash_or_return_existing_handle(key_handle)
    return key_handle


@check_for_kwargs_wrapt
def DeleteKey(key: Union[PyHKEY, int], sub_key: str) -> None:         # noqa
    """
    Deletes the specified key.
    key is an already open key, or one of the predefined HKEY_* constants.
    sub_key is a string that must be a subkey of the key identified by the key parameter or ''.
    This value must not be None, and the key may not have subkeys.
    This method can not delete keys with subkeys.
    If the method succeeds, the entire key, including all of its values, is removed.

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)

    >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)
    >>> key_handle_created = CreateKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')

    >>> # Delete key without subkeys
    >>> assert __key_in_py_hive_handles(r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz')

    >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')
    >>> assert not __key_in_py_hive_handles(r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz')

    >>> # try to delete non existing key (it was deleted before)
    >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')
    Traceback (most recent call last):
        ...
    FileNotFoundError: [WinError 2] The system cannot find the file specified

    >>> # try to delete key with subkey
    >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx')
    Traceback (most recent call last):
        ...
    PermissionError: [WinError 5] Access is denied

    >>> # try to delete key with subkey = None
    >>> DeleteKey(reg_handle, None)                     # noqa
    Traceback (most recent call last):
        ...
    TypeError: DeleteKey() argument 2 must be str, not None

    >>> # subkey = '' is allowed here
    >>> reg_handle_sub = OpenKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
    >>> DeleteKey(reg_handle_sub, '')

    >>> # Teardown
    >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx')

    """
    if not isinstance(sub_key, str):
        raise TypeError('DeleteKey() argument 2 must be str, not None')

    sub_key = str(sub_key)
    key_handle = __resolve_key(key)
    try:
        fake_reg_key = fake_reg.get_fake_reg_key(fake_reg_key=key_handle.data, sub_key=sub_key)
    except FileNotFoundError:
        error = FileNotFoundError('[WinError 2] The system cannot find the file specified')
        setattr(error, 'winerror', 2)
        raise error

    if fake_reg_key.subkeys:
        permission_error = PermissionError('[WinError 5] Access is denied')
        setattr(permission_error, 'winerror', 5)
        raise permission_error

    full_key_path = fake_reg_key.full_key
    sub_key = str(full_key_path.rsplit('\\', 1)[1])
    fake_parent_key = fake_reg_key.parent_fake_registry_key
    # get rid of Optional[] mypy
    assert fake_parent_key is not None
    fake_parent_key.subkeys.pop(sub_key, None)       # delete the subkey
    __py_hive_handles.pop(full_key_path, None)       # delete the handle from the dict, if any


@check_for_kwargs_wrapt
def DeleteKeyEx(key: Union[PyHKEY, int], sub_key: str, access: int = KEY_WOW64_64KEY, reserved: int = 0) -> None:     # noqa
    """
    Deletes the specified key.

    Note The DeleteKeyEx() function is implemented with the RegDeleteKeyEx Windows API function,
    which is specific to 64-bit versions of Windows. See the RegDeleteKeyEx documentation.

    key is an already open key, or one of the predefined HKEY_* constants.
    sub_key is a string that must be a subkey of the key identified by the key parameter.
    This value must not be None, and the key may not have subkeys.

    reserved is a reserved integer, and must be zero. The default is zero.
    access is an integer that specifies an access mask that describes the desired security
    access for the key. Default is KEY_WOW64_64KEY. See Access Rights for other allowed values. (NOT IMPLEMENTED)

    This method can not delete keys with subkeys.

    If the method succeeds, the entire key, including all of its values, is removed.
    If the method fails, an OSError exception is raised.

    On unsupported Windows versions, NotImplementedError is raised.
    Raises an auditing event winreg.DeleteKey with arguments key, sub_key, access. (NOT IMPLEMENTED)

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)
    >>> key_handle_created = CreateKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')

    >>> # Delete key without subkeys
    >>> assert __key_in_py_hive_handles(r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz')
    >>> DeleteKeyEx(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')
    >>> assert not __key_in_py_hive_handles(r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz')

    >>> # try to delete non existing key (it was deleted before)
    >>> DeleteKeyEx(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')
    Traceback (most recent call last):
        ...
    FileNotFoundError: [WinError 2] The system cannot find the file specified

    >>> # try to delete key with subkey
    >>> DeleteKeyEx(reg_handle, r'SOFTWARE\\xxxx')
    Traceback (most recent call last):
        ...
    PermissionError: [WinError 5] Access is denied

    >>> # try to delete key with subkey = None
    >>> DeleteKeyEx(reg_handle, None)            # noqa
    Traceback (most recent call last):
        ...
    TypeError: DeleteKey() argument 2 must be str, not None

    >>> # try to delete key with access = KEY_WOW64_32KEY
    >>> DeleteKeyEx(reg_handle, r'SOFTWARE\\xxxx\\yyyy', KEY_WOW64_32KEY)
    Traceback (most recent call last):
        ...
    NotImplementedError: we only support KEY_WOW64_64KEY

    >>> # Teardown
    >>> DeleteKeyEx(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
    >>> DeleteKeyEx(reg_handle, r'SOFTWARE\\xxxx')

    """
    if access == KEY_WOW64_32KEY:
        raise NotImplementedError('we only support KEY_WOW64_64KEY')
    DeleteKey(key, sub_key)


@check_for_kwargs_wrapt
def DeleteValue(key: Union[PyHKEY, int], value: Optional[str]) -> None:         # noqa
    """
    Removes a named value from a registry key.
    key is an already open key, or one of the predefined HKEY_* constants.
    value is a string that identifies the value to remove.
    if value is None, or '' it deletes the default Value of the Key
    Raises an auditing event winreg.DeleteValue with arguments key, value. (NOT IMPLEMENTED)

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)

    >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
    >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
    >>> # winreg.SetValueEx(reg_key, 'some_test', 0, winreg.REG_SZ, 'some_test_value')

    >>> # Delete Default Value, value_name NONE (not set, therefore Error
    >>> DeleteValue(key_handle, None)
    Traceback (most recent call last):
        ...
    FileNotFoundError: [WinError 2] The system cannot find the file specified

    >>> # Delete Default Value, value_name '' (not set, therefore Error
    >>> DeleteValue(key_handle, '')
    Traceback (most recent call last):
        ...
    FileNotFoundError: [WinError 2] The system cannot find the file specified

    >>> # Delete Non Existing Value
    >>> DeleteValue(key_handle, 'some_test')
    Traceback (most recent call last):
        ...
    FileNotFoundError: [WinError 2] The system cannot find the file specified

    """
    if value is None:
        value = ''

    key_handle = __resolve_key(key)
    try:
        del key_handle.data.values[value]
    except KeyError:
        error = FileNotFoundError('[WinError 2] The system cannot find the file specified')
        setattr(error, 'winerror', 2)
        raise error


@check_for_kwargs_wrapt
def EnumKey(key: Union[PyHKEY, int], index: int) -> str:              # noqa
    """
    Enumerates subkeys of an open registry key, returning a string.
    key is an already open key, or one of the predefined HKEY_* constants.
    index is an integer that identifies the index of the key to retrieve.
    The function retrieves the name of one subkey each time it is called.
    It is typically called repeatedly until an OSError exception is raised,
    indicating, no more values are available.
    Raises an auditing event winreg.EnumKey with arguments key, index. (NOT IMPLEMENTED)

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)

    >>> # test get the first profile in the profile list
    >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
    >>> assert isinstance(EnumKey(key_handle, 0), str)

    >>> # test out of index
    >>> EnumKey(key_handle, 100000000)
    Traceback (most recent call last):
        ...
    OSError: [WinError 259] No more data is available

    """
    key_handle = __resolve_key(key)
    try:
        sub_key_str = list(key_handle.data.subkeys.keys())[index]
        return sub_key_str
    except IndexError:
        error = OSError('[WinError 259] No more data is available')
        setattr(error, 'winerror', 259)
        raise error


@check_for_kwargs_wrapt
def EnumValue(key: Union[PyHKEY, int], index: int) -> Tuple[str, Union[None, bytes, str, int], int]:              # noqa
    """
    Enumerates values of an open registry key, returning a tuple.

    The result is a tuple of 3 items:
    Index       Meaning
    0           A string that identifies the value name
    1           An object that holds the value data, and whose type depends on the underlying registry type
    2           An integer giving the registry type for this value (see table in docs for SetValueEx())

    key is an already open key, or one of the predefined HKEY_* constants.
    index is an integer that identifies the index of the value to retrieve.
    The function retrieves the name of one subkey each time it is called.
    It is typically called repeatedly, until an OSError exception is raised, indicating no more values.
    Raises an auditing event winreg.EnumValue with arguments key, index. (NOT IMPLEMENTED)

    type(int)       type name                       Description
    =========================================================
    0               REG_NONE	                    No defined value type.
    1               REG_SZ	                        A null-terminated string.
    2               REG_EXPAND_SZ	                Null-terminated string containing references to environment variables (%PATH%).
                                                    (Python handles this termination automatically.)
    3               REG_BINARY	                    Binary data in any form.
    4               REG_DWORD	                    A 32-bit number.
    4               REG_DWORD_LITTLE_ENDIAN	        A 32-bit number in little-endian format.
    5               REG_DWORD_BIG_ENDIAN	        A 32-bit number in big-endian format.
    6               REG_LINK	                    A Unicode symbolic link.
    7               REG_MULTI_SZ	                A sequence of null-terminated strings, terminated by two null characters.
    8               REG_RESOURCE_LIST	            A device-driver resource list.
    9               REG_FULL_RESOURCE_DESCRIPTOR    A hardware setting.
    10              REG_RESOURCE_REQUIREMENTS_LIST  A hardware resource list.
    11              REG_QWORD                       A 64 - bit number.
    11              REG_QWORD_LITTLE_ENDIAN         A 64 - bit number in little - endian format.Equivalent to REG_QWORD.

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)

    >>> # Read the current Version
    >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
    >>> EnumValue(key_handle, 0)
    (...)

    >>> # test out of index
    >>> EnumValue(key_handle, 100000000)
    Traceback (most recent call last):
        ...
    OSError: [WinError 259] No more data is available

    """
    key_handle = __resolve_key(key)
    try:
        value_name = list(key_handle.data.values.keys())[index]
        value_data = key_handle.data.values[value_name].value
        value_type = key_handle.data.values[value_name].value_type
        return value_name, value_data, value_type
    except IndexError:
        error = OSError('[WinError 259] No more data is available')
        setattr(error, 'winerror', 259)
        raise error


# named arguments are allowed here !
def OpenKey(key: Union[PyHKEY, int], sub_key: Union[str, None], reserved: int = 0, access: int = KEY_READ) -> PyHKEY:         # noqa
    """
    Opens the specified key, returning a handle object.
    key is an already open key, or one of the predefined HKEY_* constants.
    sub_key is a string that identifies the sub_key to open.
    reserved is a reserved integer, and must be zero. The default is zero.
    access is an integer that specifies an access mask that describes the desired security access for the key.
    Default is KEY_READ. See Access Rights for other allowed values.

    The result is a new handle to the specified key.
    If the key is not found, FileNotFoundError is raised
    If the function fails, OSError is raised.
    Raises an auditing event winreg.OpenKey with arguments key, sub_key, access.    # not implemented
    Raises an auditing event winreg.OpenKey/result with argument key.               # not implemented
    Changed in version 3.2: Allow the use of named arguments.
    Changed in version 3.3: See above.

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)

    >>> # Open Key
    >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
    >>> assert key_handle.data.full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'

    >>> # Open Key mit subkey=None
    >>> reg_open1 = OpenKey(key_handle, None)

    >>> # Open Key mit subkey=''
    >>> reg_open2 = OpenKey(key_handle, '')

    >>> # Open the same kay again, but we get a different Handle
    >>> reg_open3 = OpenKey(key_handle, '')

    >>> assert reg_open2 != reg_open3

    >>> # Open non existing Key
    >>> OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\DoesNotExist')
    Traceback (most recent call last):
        ...
    FileNotFoundError: [WinError 2] The system cannot find the file specified

    """
    if sub_key is None:
        sub_key = ''

    try:
        key_handle = __resolve_key(key)
        access = key_handle.access
        reg_key = fake_reg.get_fake_reg_key(key_handle.data, sub_key=sub_key)
        key_handle = PyHKEY(reg_key, access=access)
        # no - winreg gives a new handle, even if You open the same key twice
        # this is, because You can open it once with Read Access,
        # and a second time with different access rights
        # reg_handle = self.add_handle_to_hash_list_or_return_already_existing_handle(reg_handle)
        __py_hive_handles[key_handle.data.full_key] = key_handle
        return key_handle
    except FileNotFoundError:
        error = FileNotFoundError('[WinError 2] The system cannot find the file specified')
        setattr(error, 'winerror', 2)
        raise error


# named arguments are allowed here !
def OpenKeyEx(key: Union[PyHKEY, int], sub_key: str, reserved: int = 0, access: int = KEY_READ) -> PyHKEY:        # noqa
    """
    Opens the specified key, returning a handle object.
    key is an already open key, or one of the predefined HKEY_* constants.
    sub_key is a string that identifies the sub_key to open.
    reserved is a reserved integer, and must be zero. The default is zero.
    access is an integer that specifies an access mask that describes the desired security access for the key.
    Default is KEY_READ. See Access Rights for other allowed values.

    The result is a new handle to the specified key.
    If the key is not found, FileNotFoundError is raised
    If the function fails, OSError is raised.
    Raises an auditing event winreg.OpenKey with arguments key, sub_key, access.    # not implemented
    Raises an auditing event winreg.OpenKey/result with argument key.               # not implemented
    Changed in version 3.2: Allow the use of named arguments.
    Changed in version 3.3: See above.

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)

    >>> # Open Key
    >>> key_handle = OpenKeyEx(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
    >>> assert key_handle.data.full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'

    >>> # Open non existing Key
    >>> OpenKeyEx(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\DoesNotExist')
    Traceback (most recent call last):
        ...
    FileNotFoundError: [WinError 2] The system cannot find the file specified

    """
    key_handle = OpenKey(key, sub_key, reserved, access)
    return key_handle


@check_for_kwargs_wrapt
def QueryInfoKey(key: Union[PyHKEY, int]) -> Tuple[int, int, int]:            # noqa
    """
    Returns information about a key, as a tuple.
    key is an already open key, or one of the predefined HKEY_* constants.
    The result is a tuple of 3 items:
    Index, Meaning
            0       An integer giving the number of sub keys this key has.
            1       An integer giving the number of values this key has.
            2       An integer giving when the key was last modified (if available) as 100’s of nanoseconds since Jan 1, 1601.
    Raises an auditing event winreg.QueryInfoKey with argument key. (NOT IMPLEMENTED)

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)

    >>> # Open Key
    >>> key_handle = OpenKeyEx(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')

    >>> new_reg_key_without_values = CreateKey(key_handle, 'test_without_values')
    >>> new_reg_key_with_subkeys_and_values = CreateKey(key_handle, 'test_with_subkeys_and_values')
    >>> SetValueEx(new_reg_key_with_subkeys_and_values, 'test_value_name', 0, REG_SZ, 'test_value')
    >>> new_reg_key_with_subkeys_subkey = CreateKey(new_reg_key_with_subkeys_and_values, 'subkey_of_test_with_subkeys')

    >>> # Test
    >>> QueryInfoKey(new_reg_key_without_values)
    (0, 0, ...)
    >>> QueryInfoKey(new_reg_key_with_subkeys_and_values)
    (1, 1, ...)

    >>> # Teardown
    >>> DeleteKey(key_handle, 'test_without_values')
    >>> DeleteKey(new_reg_key_with_subkeys_and_values, 'subkey_of_test_with_subkeys')
    >>> DeleteKey(key_handle, 'test_with_subkeys_and_values')
    """
    reg_handle = __resolve_key(key)
    n_subkeys = len(reg_handle.data.subkeys)
    n_values = len(reg_handle.data.values)
    last_modified_nanoseconds = reg_handle.data.last_modified_ns        # 100’s of nanoseconds since Jan 1, 1601. / 1.Jan.1970 diff = 11644473600 * 1E9
    return n_subkeys, n_values, last_modified_nanoseconds


@check_for_kwargs_wrapt
def QueryValue(key: Union[PyHKEY, int], sub_key: Union[str, None]) -> str:        # noqa
    """
    Retrieves the unnamed value for a key, as a string.
    key is an already open key, or one of the predefined HKEY_* constants.
    sub_key is a string that holds the name of the subkey with which the value is associated.
    If this parameter is None or empty, the function retrieves the value set by the SetValue()
    method for the key identified by key.
    Values in the registry have name, type, and data components.
    This method retrieves the data for a key’s first value that has a NULL name.
    But the underlying API call doesn’t return the type, so always use QueryValueEx() if possible.

    * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)"
    it is usually not set. Nethertheless, even if the value is not set, QueryValue will deliver ''

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)
    >>> key_handle_created = CreateKey(reg_handle, r'SOFTWARE\\lib_registry_test')

    >>> # read Default Value, which is ''
    >>> assert QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == ''

    >>> # sub key can be here None or empty !
    >>> assert QueryValue(key_handle_created, '') == ''
    >>> assert QueryValue(key_handle_created, None) == ''

    >>> # set and get default value
    >>> SetValueEx(key_handle_created, '', 0, REG_SZ, 'test1')
    >>> assert QueryValueEx(key_handle_created, '') == ('test1', 1)
    >>> assert QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == 'test1'

    >>> # Teardown
    >>> DeleteKey(reg_handle, r'SOFTWARE\\lib_registry_test')

    """
    key_handle = __resolve_key(key)
    key_handle = OpenKey(key_handle, sub_key)
    try:
        result = key_handle.data.values[''].value
        if not isinstance(result, str):
            error = OSError('[WinError 13] The data is invalid')
            setattr(error, 'winerror', 13)
            raise error
        isinstance(result, str)
        default_value = result
    except KeyError:
        default_value = ''

    return default_value


@check_for_kwargs_wrapt
def QueryValueEx(key: Union[PyHKEY, int], value_name: Optional[str]) -> Tuple[Union[None, bytes, str, int], int]:     # noqa
    """
    Retrieves data and type for a specified value name associated with an open registry key.
    key is an already open key, or one of the predefined HKEY_* constants.
    value_name is a string indicating the value to query. If Value_name is '' or None,
    it queries the Default Value of the Key - this will Fail if the Default Value for the Key is not Present.
    But the Default Value might be set to "None" - then "None" will be returned.

    The result is a tuple of 2 items:
    Index       Meaning
    0           The value of the registry item.
    1           An integer giving the registry type for this value (see table in docs for SetValueEx())
    Raises an auditing event winreg.QueryValue with arguments key, sub_key, value_name. (NOT Implemented)

    type(int)       type name                       Description
    =========================================================
    0               REG_NONE	                    No defined value type.
    1               REG_SZ	                        A null-terminated string.
    2               REG_EXPAND_SZ	                Null-terminated string containing references to environment variables (%PATH%).
                                                    (Python handles this termination automatically.)
    3               REG_BINARY	                    Binary data in any form.
    4               REG_DWORD	                    A 32-bit number.
    4               REG_DWORD_LITTLE_ENDIAN	        A 32-bit number in little-endian format.
    5               REG_DWORD_BIG_ENDIAN	        A 32-bit number in big-endian format.
    6               REG_LINK	                    A Unicode symbolic link.
    7               REG_MULTI_SZ	                A sequence of null-terminated strings, terminated by two null characters.
    8               REG_RESOURCE_LIST	            A device-driver resource list.
    9               REG_FULL_RESOURCE_DESCRIPTOR    A hardware setting.
    10              REG_RESOURCE_REQUIREMENTS_LIST  A hardware resource list.
    11              REG_QWORD                       A 64 - bit number.
    11              REG_QWORD_LITTLE_ENDIAN         A 64 - bit number in little - endian format.Equivalent to REG_QWORD.

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
    >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')

    >>> # Read the current Version
    >>> QueryValueEx(key_handle, 'CurrentBuild')
    ('...', 1)

    >>> # Attempt to read a non Existing Default Value
    >>> QueryValueEx(key_handle, '')
    Traceback (most recent call last):
        ...
    FileNotFoundError: [WinError 2] The system cannot find the file specified

    >>> QueryValueEx(key_handle, None)
    Traceback (most recent call last):
        ...
    FileNotFoundError: [WinError 2] The system cannot find the file specified

    >>> # Set a Default Value
    >>> SetValueEx(key_handle, '',0 , REG_SZ, 'test_default_value')
    >>> QueryValueEx(key_handle, '')
    ('test_default_value', 1)

    >>> # Delete a Default Value
    >>> DeleteValue(key_handle, None)

    """

    try:
        if value_name is None:
            value_name = ''
        key_handle = __resolve_key(key)
        value = key_handle.data.values[value_name].value
        value_type = key_handle.data.values[value_name].value_type
        return value, value_type
    except KeyError:
        error = FileNotFoundError('[WinError 2] The system cannot find the file specified')
        setattr(error, 'winerror', 2)
        raise error


@check_for_kwargs_wrapt
def SetValue(key: Union[PyHKEY, int], sub_key: Union[str, None], type: int, value: str) -> None:      # noqa
    """
    Associates a value with a specified key. (the Default Value of the Key, usually not set)
    key is an already open key, or one of the predefined HKEY_* constants.
    sub_key is a string that names the subkey with which the value is associated.
    type is an integer that specifies the type of the data. Currently this must be REG_SZ,
    meaning only strings are supported. Use the SetValueEx() function for support for other data types.
    value is a string that specifies the new value.

    If the key specified by the sub_key parameter does not exist, the SetValue function creates it.

    Value lengths are limited by available memory. Long values (more than 2048 bytes) should be stored
    as files with the filenames stored in the configuration registry. This helps the registry perform efficiently.
    The key identified by the key parameter must have been opened with KEY_SET_VALUE access.    (NOT IMPLEMENTED)
    Raises an auditing event winreg.SetValue with arguments key, sub_key, type, value.          (NOT IMPLEMENTED)

    * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)"
    it is usually not set. Nethertheless, even if the value is not set, QueryValue will deliver ''

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)
    >>> key_handle = CreateKey(reg_handle, r'SOFTWARE\\lib_registry_test')

    >>> # read Default Value, which is ''
    >>> assert QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == ''

    >>> # sub key can be ''
    >>> SetValue(key_handle, '', REG_SZ, 'test1')
    >>> assert QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == 'test1'

    >>> # sub key can be None
    >>> SetValue(key_handle, None, REG_SZ, 'test2')
    >>> assert QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == 'test2'

    >>> # use sub key
    >>> reg_handle_software = OpenKey(reg_handle, 'SOFTWARE')
    >>> SetValue(reg_handle_software, 'lib_registry_test', REG_SZ, 'test3')
    >>> assert QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == 'test3'

    >>> # Tear Down
    >>> DeleteKey(reg_handle,r'SOFTWARE\\lib_registry_test')

    """
    if type != REG_SZ:
        # checked - like winreg
        raise TypeError('type must be winreg.REG_SZ')

    key_handle = __resolve_key(key)
    access = key_handle.access
    try:
        # create the key if not there
        key_handle = OpenKey(key_handle, sub_key, 0, access=access)
    except FileNotFoundError:
        key_handle = CreateKey(key_handle, sub_key)
    SetValueEx(key_handle, '', 0, REG_SZ, value)


@check_for_kwargs_wrapt
def SetValueEx(key: Union[PyHKEY, int], value_name: Optional[str], reserved: int, type: int, value: Union[None, bytes, str, int]) -> None:    # noqa
    """
    Stores data in the value field of an open registry key.
    key is an already open key, or one of the predefined HKEY_* constants.

    value_name is a string that names the subkey with which the value is associated.
    if value_name is None or '' it will write to the default value of the Key

    reserved can be anything – zero is always passed to the API.

    type is an integer that specifies the type of the data.

    value is a new value.

    This method can also set additional value and type information for the specified key.
    The key identified by the key parameter must have been opened with KEY_SET_VALUE access.    (NOT IMPLEMENTED))

    To open the key, use the CreateKey() or OpenKey() methods.

    Value lengths are limited by available memory. Long values (more than 2048 bytes)
    should be stored as files with the filenames stored in the configuration registry. This helps the registry perform efficiently.
    Raises an auditing event winreg.SetValue with arguments key, sub_key, type, value.          (NOT IMPLEMENTED)

    type(int)       type name                       Description
    =========================================================
    0               REG_NONE	                    No defined value type.
    1               REG_SZ	                        A null-terminated string.
    2               REG_EXPAND_SZ	                Null-terminated string containing references to environment variables (%PATH%).
                                                    (Python handles this termination automatically.)
    3               REG_BINARY	                    Binary data in any form.
    4               REG_DWORD	                    A 32-bit number.
    4               REG_DWORD_LITTLE_ENDIAN	        A 32-bit number in little-endian format.
    5               REG_DWORD_BIG_ENDIAN	        A 32-bit number in big-endian format.
    6               REG_LINK	                    A Unicode symbolic link.
    7               REG_MULTI_SZ	                A sequence of null-terminated strings, terminated by two null characters.
    8               REG_RESOURCE_LIST	            A device-driver resource list.
    9               REG_FULL_RESOURCE_DESCRIPTOR    A hardware setting.
    10              REG_RESOURCE_REQUIREMENTS_LIST  A hardware resource list.
    11              REG_QWORD                       A 64 - bit number.
    11              REG_QWORD_LITTLE_ENDIAN         A 64 - bit number in little - endian format.Equivalent to REG_QWORD.


    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
    >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')

    >>> # Test
    >>> SetValueEx(key_handle, 'some_test', 0, REG_SZ, 'some_test_value')
    >>> assert QueryValueEx(key_handle, 'some_test') == ('some_test_value', REG_SZ)

    >>> # Test Overwrite
    >>> SetValueEx(key_handle, 'some_test', 0, REG_SZ, 'some_test_value2')
    >>> assert QueryValueEx(key_handle, 'some_test') == ('some_test_value2', REG_SZ)

    >>> # Teardown
    >>> DeleteValue(key_handle, 'some_test')

    """
    # Todo : Raise Errors according to winreg - check types of value against type of REG_*
    # and make test matrix for it
    # Example Error from Winreg :
    # TypeError: Objects of type 'str' can not be used as binary registry values (if try to write string to REG_NONE type)

    # value name = None is the default Value of the Key
    if value_name is None:
        value_name = ''
    key_handle = __resolve_key(key)
    fake_reg.set_fake_reg_value(key_handle.data, sub_key='', value_name=value_name, value=value, value_type=type)


def __resolve_key(key: Union[int, PyHKEY]) -> PyHKEY:
    """
    Returns the full path to the key

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)

    >>> # Connect
    >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)

    >>> __resolve_key(key=reg_handle).data.full_key
    'HKEY_CURRENT_USER'

    >>> __resolve_key(key=HKEY_CURRENT_USER).data.full_key
    'HKEY_CURRENT_USER'

    """

    if isinstance(key, int):
        key_handle = PyHKEY(__fake_registry.hive[key])
    else:
        key_handle = key
    return key_handle


def __add_key_handle_to_hash_or_return_existing_handle(key_handle: PyHKEY) -> PyHKEY:
    if key_handle.data.full_key in __py_hive_handles:
        key_handle = __py_hive_handles[key_handle.data.full_key]
    else:
        __py_hive_handles[key_handle.data.full_key] = key_handle
    return key_handle


def __key_in_py_hive_handles(key: str) -> bool:
    global __py_hive_handles
    if key in __py_hive_handles:
        return True
    else:
        return False
