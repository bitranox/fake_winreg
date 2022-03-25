# STDLIB
from types import TracebackType
from typing import Any, Callable, Optional, Tuple, Type, TypeVar, Union, cast
import inspect
import threading

# EXT
import wrapt

# OWN
try:
    from .types_custom import RegData
    from .registry_constants import *
    from . import fake_reg
    from . import fake_reg_tools
    from . import helpers
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    # imports for doctest
    from registry_constants import *  # type: ignore  # pragma: no cover
    from types_custom import RegData  # type: ignore  # pragma: no cover
    import fake_reg  # type: ignore  # pragma: no cover
    import fake_reg_tools  # type: ignore  # pragma: no cover
    import helpers  # type: ignore  # pragma: no cover

F = TypeVar("F", bound=Callable[..., Any])

# we start around 600 like winreg - this will be incremented every time a new handle is acquired
_last_int_handle: int = 600
# lock for incrementing the unique _int_handle
_last_int_handle_lock = threading.Lock()


@wrapt.decorator
def check_for_kwargs_wrapt(wrapped: F, instance: object = None, args: Any = (), kwargs: Any = dict()) -> F:  # noqa
    if kwargs:  # pragma: no cover
        keys = ", ".join([key for key in kwargs.keys()])  # pragma: no cover
        raise TypeError(f"{wrapped.__name__}() got some positional-only arguments passed as keyword arguments: '{keys}'")  # pragma: no cover
    return cast(F, wrapped(*args, **kwargs))


class HKEYType(object):
    def __init__(self, handle: fake_reg.FakeRegistryKey, access: int = KEY_READ):
        """
        >>> hkey = HKEYType(handle=fake_reg.FakeRegistryKey())
        >>> assert int(hkey) != 0

        """
        self.handle = handle
        self._access = access
        global _last_int_handle
        with _last_int_handle_lock:
            _last_int_handle = _last_int_handle + 1
            self._int_handle = _last_int_handle

    def __int__(self) -> int:
        return self._int_handle

    @staticmethod
    def Close() -> None:  # noqa
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


class PyHKEY(HKEYType):
    """
    Registry Handle Objects
    This object wraps a Windows HKEY object, automatically closing it when the object is destroyed.
    To guarantee cleanup, you can call either the Close() method on the object, or the CloseKey() function.
    All registry functions in this module return one of these objects.

    This wrapper can also be used as a context manager, to guarantee that the key will be closed after use.

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

    def __init__(self, handle: fake_reg.FakeRegistryKey, access: int = KEY_READ):
        super().__init__(handle, access)

    def __enter__(self) -> "PyHKEY":
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]) -> None:
        self.Close()


# DataTypesHandle{{{

# the possible types of a handle that can be passed to winreg functions
Handle = Union[int, HKEYType, PyHKEY]

# DataTypesHandle}}}

__fake_registry = fake_reg.FakeRegistry()


def load_fake_registry(fake_registry: fake_reg.FakeRegistry) -> None:
    global __fake_registry
    __fake_registry = fake_registry


@check_for_kwargs_wrapt
# CloseKey{{{
def CloseKey(hkey: Union[int, HKEYType]) -> None:  # noqa
    """
    Closes a previously opened registry key.

    the function does NOT accept named parameters, only positional parameters

    Note: If hkey is not closed using this method (or via hkey.Close()), it is closed when the hkey object is destroyed by Python.



    Parameter
    ---------

    hkey:
        the predefined handle to connect to, or one of the predefined HKEY_* constants.



    Exceptions
    ----------

    OSError: [WinError 6] The handle is invalid
        if parameter key is invalid

    TypeError: The object is not a PyHKEY object
        if parameter key is not integer or PyHKEY type

    OverflowError: int too big to convert
        if parameter key is > 64 Bit Integer Value

    TypeError: CloseKey() got some positional-only arguments passed as keyword arguments: '<key>'
        if a keyword (named) parameter was passed



    Examples
    --------

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)

    >>> # Test
    >>> hive_key = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
    >>> CloseKey(HKEY_LOCAL_MACHINE)

    >>> # Test hkey = None
    >>> hive_key = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
    >>> CloseKey(None)  # noqa

    >>> # does not accept keyword parameters
    >>> hive_key = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
    >>> CloseKey(hkey=HKEY_LOCAL_MACHINE)
    Traceback (most recent call last):
        ...
    TypeError: CloseKey() got some positional-only arguments passed as keyword arguments: 'hkey'

    """
    # CloseKey}}}

    if hkey is not None:  # None accepted here
        __check_key(hkey)
    # we could recursively delete all the handles in self.py_hkey_handles by walking the fake registry keys
    # or we can get the hive name and delete all self.py_hkey_handles beginning with hive name
    # the objects are destroyed anyway when we close fake_winreg object, so we dont bother


@check_for_kwargs_wrapt
# ConnectRegistry{{{
def ConnectRegistry(computer_name: Optional[str], key: Handle) -> PyHKEY:  # noqa
    """
    Establishes a connection to a predefined registry handle on another computer, and returns a new handle object.
    the function does NOT accept named parameters, only positional parameters



    Parameter
    ---------

    computer_name:
        the name of the remote computer, of the form r"\\computername" or simply "computername"
        If None or '', the local computer is used.

        if the computer name can not be resolved on the network,fake_winreg will deliver:
         "OSError: [WinError 1707] The network address is invalid"

        if the computer_name given can be reached, we finally raise:
        "SystemError: System error 53 has occurred. The network path was not found"


    key:
        the predefined handle to connect to, or one of the predefined HKEY_* constants.



    Returns
    -------

    the handle of the opened key. If the function fails, an OSError exception is raised.



    Exceptions
    ----------

    OSError: [WinError 1707] The network address is invalid
        if the computer name can not be resolved

    FileNotFoundError: [WinError 53] The network path was not found
        if the network path is invalid

    OSError: [WinError 6] The handle is invalid
        if parameter key is invalid

    TypeError: None is not a valid HKEY in this context
        if parameter key is None


    TypeError: The object is not a PyHKEY object
        if parameter key is not integer or PyHKEY type

    OverflowError: int too big to convert
        if parameter key is > 64 Bit Integer Value

    TypeError: ConnectRegistry() got some positional-only arguments passed as keyword arguments: '<key>'
        if a keyword (named) parameter was passed



    Events
    ------

    winreg.ConnectRegistry auditing event (NOT IMPLEMENTED), with arguments computer_name, key.



    Examples
    --------

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)

    >>> # Connect
    >>> ConnectRegistry(None, HKEY_LOCAL_MACHINE)
    <...PyHKEY object at ...>

    >>> # Try to connect to computer
    >>> ConnectRegistry('HAL', HKEY_LOCAL_MACHINE)
    Traceback (most recent call last):
        ...
    OSError: [WinError 1707] The network address is invalid

    >>> # Try connect to computer, but invalid network path
    >>> ConnectRegistry(r'localhost\\invalid\\path', HKEY_LOCAL_MACHINE)
    Traceback (most recent call last):
        ...
    FileNotFoundError: [WinError 53] The network path was not found

    >>> # provoke wrong key type Error
    >>> ConnectRegistry('fake_registry_test_computer', 'fake_registry_key')  # noqa
    Traceback (most recent call last):
        ...
    TypeError: The object is not a PyHKEY object

    >>> # provoke Invalid Handle Error
    >>> ConnectRegistry(None, 42)
    Traceback (most recent call last):
        ...
    OSError: [WinError 6] The handle is invalid

    >>> # must not accept keyword parameters
    >>> ConnectRegistry(computer_name=None, key=HKEY_LOCAL_MACHINE)
    Traceback (most recent call last):
        ...
    TypeError: ConnectRegistry() got some positional-only arguments passed as keyword arguments: 'computer_name, key'

    """
    # ConnectRegistry}}}

    __check_key(key)

    if computer_name:
        if helpers.is_computer_reachable(computer_name):
            # SystemError: System error 53 has occurred. The network path was not found
            system_error = FileNotFoundError("[WinError 53] The network path was not found")
            setattr(system_error, "winerror", 53)
            raise system_error
        else:
            # OSError: [WinError 1707] The network address is invalid
            network_error = OSError("[WinError 1707] The network address is invalid")
            setattr(network_error, "winerror", 1707)
            raise network_error

    try:
        fake_reg_handle = __fake_registry.hive[key]
    except KeyError:
        error = OSError("[WinError 6] The handle is invalid")
        setattr(error, "winerror", 6)
        raise error

    hive_handle = PyHKEY(handle=fake_reg_handle)
    return hive_handle


@check_for_kwargs_wrapt
# CreateKey{{{
def CreateKey(key: Handle, sub_key: Optional[str]) -> PyHKEY:  # noqa
    """
    Creates or opens the specified key.

    The sub_key can contain a directory structure like r'Software\\xxx\\yyy' - all the parents to yyy will be created

    the function does NOT accept named parameters, only positional parameters


    Result
    ------

    If key is one of the predefined keys, sub_key may be None or empty string,
    and a new handle will be returned with access KEY_WRITE

    If the key already exists, this function opens the existing key.
    otherwise it will return the handle to the new created key with access KEY_WRITE


    From original winreg description (this is wrong):
        If key is one of the predefined keys, sub_key may be None.
        In that case, the handle returned is the same key handle passed in to the function.
        I always get back a different handle, this seems to be wrong (needs testing)

    Parameter
    ---------

    key:
        an already open key, or one of the predefined HKEY_* constants.

    sub_key:
        a string that names the key this method opens or creates.
        sub_key can be None or empty string when the key is one of the predefined hkeys


    Exceptions
    ----------

    PermissionError: [WinError 5] Access is denied
        if You dont have the right to Create the Key (at least KEY_CREATE_SUBKEY)

    OSError: [WinError 1010] The configuration registry key is invalid
        if the function fails to create the Key

    OSError: [WinError 6] The handle is invalid
        if parameter key is invalid

    TypeError: None is not a valid HKEY in this context
        if parameter key is None

    TypeError: The object is not a PyHKEY object
        if parameter key is not integer or PyHKEY type

    OverflowError: int too big to convert
        if parameter key is > 64 Bit Integer Value

    TypeError: CreateKey() argument 2 must be str or None, not <type>
        if the subkey is anything else then str or None

    OSError: [WinError 1010] The configuration registry key is invalid
        if the subkey is None or empty string, and key is not one of the predefined HKEY Constants

    TypeError: CreateKey() got some positional-only arguments passed as keyword arguments: '<key>'
        if a keyword (named) parameter was passed



    Events
    ------

    Raises an auditing event winreg.CreateKey with arguments key, sub_key, access. (NOT IMPLEMENTED)

    Raises an auditing event winreg.OpenKey/result with argument key. (NOT IMPLEMENTED)



    Examples
    --------

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)

    >>> # Connect
    >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)

    >>> # create key
    >>> key_handle_created = CreateKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')

    >>> # create an existing key - we should NOT get the same handle back
    >>> key_handle_existing = CreateKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
    >>> assert key_handle_existing != key_handle_created

    >>> # provoke Error key None
    >>> CreateKey(None, r'SOFTWARE\\xxxx\\yyyy')    # noqa
    Traceback (most recent call last):
        ...
    TypeError: None is not a valid HKEY in this context

    >>> # provoke Error key wrong type
    >>> CreateKey('test_fake_key_invalid', r'SOFTWARE\\xxxx\\yyyy')    # noqa
    Traceback (most recent call last):
        ...
    TypeError: The object is not a PyHKEY object

    >>> # provoke Error key >= 2 ** 64
    >>> CreateKey(2 ** 64, r'SOFTWARE\\xxxx\\yyyy')
    Traceback (most recent call last):
        ...
    OverflowError: int too big to convert

    >>> # provoke invalid handle
    >>> CreateKey(42, r'SOFTWARE\\xxxx\\yyyy')
    Traceback (most recent call last):
    ...
    OSError: [WinError 6] The handle is invalid

    >>> # provoke Error on empty subkey
    >>> key_handle_existing = CreateKey(key_handle_created, r'')
    Traceback (most recent call last):
        ...
    OSError: [WinError 1010] The configuration registry key is invalid

    >>> # provoke Error subkey wrong type
    >>> key_handle_existing = CreateKey(reg_handle, 1)  # noqa
    Traceback (most recent call last):
        ...
    TypeError: CreateKey() argument 2 must be str or None, not int

    >>> # Test subkey=None with key as predefined HKEY - that should pass
    >>> # the actual behaviour is different to the winreg documentation !
    >>> key_handle_hkcu = CreateKey(HKEY_CURRENT_USER, None)
    >>> key_handle_hkcu2 = CreateKey(key_handle_hkcu, None)
    >>> assert key_handle_hkcu != key_handle_hkcu2

    >>> # Test subkey='' with key as predefined HKEY - that should pass
    >>> # the actual behaviour is different to the winreg documentation !
    >>> key_handle_hkcu = CreateKey(HKEY_CURRENT_USER, '')
    >>> key_handle_hkcu2 = CreateKey(key_handle_hkcu, '')
    >>> assert key_handle_hkcu != key_handle_hkcu2

    >>> # Teardown
    >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
    >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx')

    """
    # CreateKey}}}

    l_predefined_hkeys = [
        "HKEY_CLASSES_ROOT",
        "HKEY_CURRENT_CONFIG",
        "HKEY_CURRENT_USER",
        "HKEY_DYN_DATA",
        "HKEY_LOCAL_MACHINE",
        "HKEY_PERFORMANCE_DATA",
        "HKEY_USERS",
    ]

    __check_key(key)
    __check_argument_must_be_str_or_none(2, sub_key)

    key_handle = __resolve_key(key)
    original_access = key_handle._access

    # if the key is not a root key, and subkey is None or '' - Raise Error
    if key_handle.handle.full_key not in l_predefined_hkeys and not sub_key:
        __raise_os_error_1010()

    fake_reg_key = fake_reg.set_fake_reg_key(key_handle.handle, sub_key=sub_key)
    # TODO : check Access and give back a handle with access KEY_WRITE (?) or actual access | KEY_WRITE ?
    # TODO : this needs to be investigated, ATM we give back actual access | KEY_WRITE that seems logical
    # TODO : investigate which access rights the returned Handle has, if subkey = None
    key_handle = PyHKEY(fake_reg_key, access=original_access | KEY_WRITE)
    # No - we give back always a new handle, that seems to be correct,
    # even if winreg documentation states it otherwise !
    # also this would not work with access rights - then we would need a new hash which includes also
    # the access rights - we can not have the same PyHkey handle with different access rights
    # key_handle = __add_key_handle_to_hash_or_return_existing_handle(key_handle)
    # __py_hive_handles[key_handle.handle.full_key] = key_handle
    return key_handle


@check_for_kwargs_wrapt
# CreateKeyEx{{{
def CreateKeyEx(key: Handle, sub_key: str, reserved: int = 0, access: int = KEY_WRITE) -> PyHKEY:  # noqa
    """
    Creates or opens the specified key, returning a handle object with access as passed in the parameter

    The sub_key can contain a directory structure like r'Software\\xxx\\yyy' - all the parents to yyy will be created

    the function does NOT accept named parameters, only positional parameters



    Parameter
    ---------

    key:
        an already open key, or one of the predefined HKEY_* constants.

    sub_key:
        a string (can be empty) that names the key this method opens or creates.
        the sub_key must not be None.

    reserved:
        reserved is a reserved integer, and has to be zero. The default is zero.

    access:
        a integer that specifies an access mask that describes the desired security access for returned key handle
        Default is KEY_WRITE. See Access Rights for other allowed values.
        (any integer is accepted here in original winreg, bit masked against KEY_* access parameters)


    Returns
    -------

    the handle of the opened key.



    Exceptions
    ----------

    OSError: [WinError 1010] The configuration registry key is invalid
        if the function fails to create the Key

    OSError: [WinError 6] The handle is invalid
        if parameter key is invalid

    TypeError: None is not a valid HKEY in this context
        if parameter key is None

    TypeError: The object is not a PyHKEY object
        if parameter key is not integer or PyHKEY type

    OverflowError: int too big to convert
        if parameter key is > 64 Bit Integer Value

    OSError: [WinError 1010] The configuration registry key is invalid
        if the subkey is None

    TypeError: CreateKeyEx() argument 2 must be str or None, not <type>
        if the subkey is anything else then str

    TypeError: CreateKeyEx() got some positional-only arguments passed as keyword arguments: '<key>'
        if a keyword (named) parameter was passed



    Events
    ------

    Raises an auditing event winreg.CreateKey with arguments key, sub_key, access. (NOT IMPLEMENTED)

    Raises an auditing event winreg.OpenKey/result with argument key. (NOT IMPLEMENTED)



    Examples
    --------

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)

    >>> # Connect
    >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)

    >>> # create key
    >>> key_handle_created = CreateKeyEx(reg_handle, r'SOFTWARE\\xxxx\\yyyy', 0, KEY_WRITE)

    >>> # create an existing key - we get a new handle back
    >>> key_handle_existing = CreateKeyEx(reg_handle, r'SOFTWARE\\xxxx\\yyyy', 0, KEY_WRITE)
    >>> assert key_handle_existing != key_handle_created

    >>> # provoke Error key None
    >>> CreateKeyEx(None, r'SOFTWARE\\xxxx\\yyyy', 0 ,  KEY_WRITE)   # noqa
    Traceback (most recent call last):
        ...
    TypeError: None is not a valid HKEY in this context

    >>> # provoke Error key wrong type
    >>> CreateKeyEx('test_fake_key_invalid', r'SOFTWARE\\xxxx\\yyyy', 0 ,  KEY_WRITE)  # noqa
    Traceback (most recent call last):
        ...
    TypeError: The object is not a PyHKEY object

    >>> # provoke Error key >= 2 ** 64
    >>> CreateKeyEx(2 ** 64, r'SOFTWARE\\xxxx\\yyyy', 0 ,  KEY_WRITE)
    Traceback (most recent call last):
        ...
    OverflowError: int too big to convert

    >>> # provoke invalid handle
    >>> CreateKeyEx(42, r'SOFTWARE\\xxxx\\yyyy', 0 ,  KEY_WRITE)
    Traceback (most recent call last):
    ...
    OSError: [WinError 6] The handle is invalid

    >>> # subkey empty is valid
    >>> discard = key_handle_existing = CreateKeyEx(reg_handle, r'', 0 ,  KEY_WRITE)

    >>> # subkey None is invalid
    >>> discard = key_handle_existing = CreateKeyEx(reg_handle, None, 0 ,  KEY_WRITE)  # noqa
    Traceback (most recent call last):
        ...
    OSError: [WinError 1010] The configuration registry key is invalid


    >>> # provoke Error subkey wrong type
    >>> key_handle_existing = CreateKeyEx(reg_handle, 1, 0 ,  KEY_WRITE)  # noqa
    Traceback (most recent call last):
        ...
    TypeError: CreateKeyEx() argument 2 must be str or None, not int

    >>> # Teardown
    >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
    >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx')

    """
    # CreateKeyEx}}}

    __check_key(key)
    __check_argument_must_be_str_or_none(2, sub_key)
    __check_reserved(reserved)
    __check_access(access)

    # checked - like winreg, the Subkey must not be None, but can be blank
    if sub_key is None:
        __raise_os_error_1010()

    key_handle = __resolve_key(key)
    access = key_handle._access
    # TODO : check Access and give back a handle with access KEY_WRITE (?) or actual access | KEY_WRITE ?
    # TODO : this needs to be investigated ! ATM we give back with access stated in the parameter - seems logical

    fake_reg_key = fake_reg.set_fake_reg_key(key_handle.handle, sub_key=sub_key)
    key_handle = PyHKEY(fake_reg_key, access=access)
    # __py_hive_handles[key_handle.handle.full_key] = key_handle
    return key_handle


@check_for_kwargs_wrapt
# DeleteKey{{{
def DeleteKey(key: Handle, sub_key: str) -> None:  # noqa
    """
    Deletes the specified key. This method can not delete keys with subkeys.
    If the method succeeds, the entire key, including all of its values, is removed.
    the function does NOT accept named parameters, only positional parameters

    Parameter
    ---------

    key:
        an already open key, or one of the predefined HKEY_* constants.

    sub_key:
        a string that must be a subkey of the key identified by the key parameter or ''.
        sub_key must not be None, and the key may not have subkeys.



    Exceptions
    ----------

    OSError ...
        if it fails to Delete the Key

    PermissionError: [WinError 5] Access is denied
        if the key specified to be deleted have subkeys

    FileNotFoundError: [WinError 2] The system cannot find the file specified
        if the Key specified to be deleted does not exist

    TypeError: DeleteKey() argument 2 must be str, not <type>
        if parameter sub_key type is anything else but string

    OSError: [WinError 6] The handle is invalid
        if parameter key is invalid

    TypeError: None is not a valid HKEY in this context
        if parameter key is None

    TypeError: The object is not a PyHKEY object
        if parameter key is not integer or PyHKEY type

    OverflowError: int too big to convert
        if parameter key is > 64 Bit Integer Value

    TypeError: DeleteKey() got some positional-only arguments passed as keyword arguments: '<key>'
        if a keyword (named) parameter was passed



    Events
    ------

    Raises an auditing event winreg.DeleteKey with arguments key, sub_key, access. (NOT IMPLEMENTED)



    Examples
    --------

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)

    >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)
    >>> key_handle_created = CreateKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')

    >>> # Delete key without subkeys
    >>> # assert __key_in_py_hive_handles(r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz')

    >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')
    >>> # assert not __key_in_py_hive_handles(r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz')

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

    >>> # provoke error subkey = None
    >>> DeleteKey(reg_handle, None)  # noqa
    Traceback (most recent call last):
        ...
    TypeError: DeleteKey() argument 2 must be str, not None

    >>> # subkey = '' is allowed here
    >>> reg_handle_sub = OpenKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
    >>> DeleteKey(reg_handle_sub, '')

    >>> # Teardown
    >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx')

    """
    # DeleteKey}}}

    __check_key(key)
    __check_argument_must_be_type_expected(arg_number=2, argument=sub_key, type_expected=str)

    sub_key = str(sub_key)
    key_handle = __resolve_key(key)
    try:
        fake_reg_key = fake_reg.get_fake_reg_key(fake_reg_key=key_handle.handle, sub_key=sub_key)
    except FileNotFoundError:
        error = FileNotFoundError("[WinError 2] The system cannot find the file specified")
        setattr(error, "winerror", 2)
        raise error

    if fake_reg_key.subkeys:
        __raise_permission_error()

    full_key_path = fake_reg_key.full_key
    sub_key = str(full_key_path.rsplit("\\", 1)[1])
    fake_parent_key = fake_reg_key.parent_fake_registry_key
    # get rid of Optional[] mypy
    assert fake_parent_key is not None
    fake_parent_key.subkeys.pop(sub_key, None)  # delete the subkey


@check_for_kwargs_wrapt
# DeleteKeyEx{{{
def DeleteKeyEx(key: Handle, sub_key: str, access: int = KEY_WOW64_64KEY, reserved: int = 0) -> None:  # noqa
    """
    Deletes the specified key. This method can not delete keys with subkeys.
    If the method succeeds, the entire key, including all of its values, is removed.
    the function does NOT accept named parameters, only positional parameters

    Note The DeleteKeyEx() function is implemented with the RegDeleteKeyEx Windows API function,
    which is specific to 64-bit versions of Windows. See the RegDeleteKeyEx documentation.



    Parameter
    ---------

    key:
        an already open key, or one of the predefined HKEY_* constants.

    sub_key:
        a string that must be a subkey of the key identified by the key parameter or ''.
        sub_key must not be None, and the key may not have subkeys.

    access:
        a integer that specifies an access mask that describes the desired security access for the key.
        Default is KEY_WOW64_64KEY. See Access Rights for other allowed values. (NOT IMPLEMENTED)
        (any integer is accepted here in original winreg

    reserved:
        reserved is a reserved integer, and must be zero. The default is zero.



    Exceptions
    ----------

    OSError: ...
        if it fails to Delete the Key

    PermissionError: [WinError 5] Access is denied
        if the key specified to be deleted have subkeys

    FileNotFoundError: [WinError 2] The system cannot find the file specified
        if the Key specified to be deleted does not exist

    OSError: [WinError 6] The handle is invalid
        if parameter key is invalid

    TypeError: None is not a valid HKEY in this context
        if parameter key is None

    TypeError: The object is not a PyHKEY object
        if parameter key is not integer or PyHKEY type

    OverflowError: int too big to convert
        if parameter key is > 64 Bit Integer Value

    NotImplementedError:
        On unsupported Windows versions (NOT IMPLEMENTED)

    TypeError: DeleteKeyEx() argument 2 must be str, not <type>
        if parameter sub_key type is anything else but string

    TypeError: an integer is required (got NoneType)
        if parameter access is None

    TypeError: an integer is required (got type <type>)
        if parameter access is not int

    OverflowError: Python int too large to convert to C long
        if parameter access is > 64 Bit Integer Value

    TypeError: an integer is required (got type <type>)
        if parameter reserved is not int

    OverflowError: Python int too large to convert to C long
        if parameter reserved is > 64 Bit Integer Value

    OSError: WinError 87 The parameter is incorrect
        if parameter reserved is not 0

    TypeError: DeleteKeyEx() got some positional-only arguments passed as keyword arguments: '<key>'
        if a keyword (named) parameter was passed



    Events
    ------

    Raises an auditing event winreg.DeleteKey with arguments key, sub_key, access. (NOT IMPLEMENTED)



    Examples
    --------

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)
    >>> key_handle_created = CreateKey(reg_handle, r'Software\\xxxx\\yyyy\\zzz')

    >>> # Delete key without subkeys
    >>> # assert __key_in_py_hive_handles(r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz')
    >>> DeleteKeyEx(reg_handle, r'Software\\xxxx\\yyyy\\zzz')
    >>> # assert not __key_in_py_hive_handles(r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz')

    >>> # try to delete non existing key (it was deleted before)
    >>> DeleteKeyEx(reg_handle, r'Software\\xxxx\\yyyy\\zzz')
    Traceback (most recent call last):
        ...
    FileNotFoundError: [WinError 2] The system cannot find the file specified

    >>> # try to delete key with subkey
    >>> DeleteKeyEx(reg_handle, r'Software\\xxxx')
    Traceback (most recent call last):
        ...
    PermissionError: [WinError 5] Access is denied

    >>> # try to delete key with subkey = None
    >>> DeleteKeyEx(reg_handle, None)            # noqa
    Traceback (most recent call last):
        ...
    TypeError: DeleteKeyEx() argument 2 must be str, not None

    >>> # try to delete key with access = KEY_WOW64_32KEY
    >>> DeleteKeyEx(reg_handle, r'Software\\xxxx\\yyyy', KEY_WOW64_32KEY)
    Traceback (most recent call last):
        ...
    NotImplementedError: we only support KEY_WOW64_64KEY

    >>> # Teardown
    >>> DeleteKeyEx(reg_handle, r'Software\\xxxx\\yyyy')
    >>> DeleteKeyEx(reg_handle, r'Software\\xxxx')

    """
    # DeleteKeyEx}}}

    __check_key(key)
    __check_argument_must_be_type_expected(arg_number=2, argument=sub_key, type_expected=str)
    __check_access(access=access)
    __check_reserved(reserved=reserved)

    if access == KEY_WOW64_32KEY:
        raise NotImplementedError("we only support KEY_WOW64_64KEY")
    DeleteKey(key, sub_key)


@check_for_kwargs_wrapt
# DeleteValue{{{
def DeleteValue(key: Handle, value: Optional[str]) -> None:  # noqa
    """
    Removes a named value from a registry key.
    the function does NOT accept named parameters, only positional parameters



    Parameter
    ---------

    key:
        an already open key, or one of the predefined HKEY_* constants.

    value:
        None, or a string that identifies the value to remove.
        if value is None, or '' it deletes the default Value of the Key



    Exceptions
    ----------

    FileNotFoundError: [WinError 2] The system cannot find the file specified'
        if the Value specified to be deleted does not exist

    OSError: [WinError 6] The handle is invalid
        if parameter key is invalid

    TypeError: None is not a valid HKEY in this context
        if parameter key is None

    TypeError: The object is not a PyHKEY object
        if parameter key is not integer or PyHKEY type

    OverflowError: int too big to convert
        if parameter key is > 64 Bit Integer Value

    TypeError: DeleteValue() argument 2 must be str or None, not <type>
        if parameter value type is anything else but string or None

    TypeError: DeleteValue() got some positional-only arguments passed as keyword arguments: '<key>'
        if a keyword (named) parameter was passed



    Events
    ------

    Raises an auditing event winreg.DeleteValue with arguments key, value. (NOT IMPLEMENTED)



    Examples
    --------

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)

    >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
    >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
    >>> SetValueEx(key_handle, 'some_test', 0, REG_SZ, 'some_test_value')

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

    """
    # DeleteValue}}}

    __check_key(key)
    __check_argument_must_be_str_or_none(2, value)

    if value is None:
        value = ""

    key_handle = __resolve_key(key)
    try:
        del key_handle.handle.values[value]
    except KeyError:
        error = FileNotFoundError("[WinError 2] The system cannot find the file specified")
        setattr(error, "winerror", 2)
        raise error


@check_for_kwargs_wrapt
# EnumKey{{{
def EnumKey(key: Handle, index: int) -> str:  # noqa
    """
    Enumerates subkeys of an open registry key, returning a string.
    The function retrieves the name of one subkey each time it is called.
    It is typically called repeatedly until an OSError exception is raised,
    indicating, no more values are available.
    the function does NOT accept named parameters, only positional parameters



    Parameter
    ---------

    key:
        an already open key, or one of the predefined HKEY_* constants.

    index:
        an integer that identifies the index of the key to retrieve.



    Exceptions:
    -----------

    OSError: [WinError 259] No more data is available
        if the index is out of Range

    OSError: [WinError 6] The handle is invalid
        if parameter key is invalid

    TypeError: None is not a valid HKEY in this context
        if parameter key is None

    TypeError: The object is not a PyHKEY object
        if parameter key is not integer or PyHKEY type

    OverflowError: int too big to convert
        if parameter key is > 64 Bit Integer Value

    TypeError: an integer is required (got type <type>)
        if parameter index is type different from int

    OverflowError: Python int too large to convert to C int
        if parameter index is > 64 Bit Integer Value

    TypeError: EnumKey() got some positional-only arguments passed as keyword arguments: '<key>'
        if a keyword (named) parameter was passed



    Events
    ------

    Raises an auditing event winreg.EnumKey with arguments key, index. (NOT IMPLEMENTED)



    Examples
    --------

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)

    >>> # test get the first profile in the profile list
    >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
    >>> assert isinstance(EnumKey(key_handle, 0), str)

    >>> # provoke error test out of index
    >>> EnumKey(key_handle, 100000000)
    Traceback (most recent call last):
        ...
    OSError: [WinError 259] No more data is available

    >>> # provoke error wrong key handle
    >>> EnumKey(42, 0)
    Traceback (most recent call last):
        ...
    OSError: [WinError 6] The handle is invalid

    >>> # no check for overflow here !
    >>> EnumKey(2 ** 64, 0)
    Traceback (most recent call last):
        ...
    OverflowError: int too big to convert

    """
    # EnumKey}}}

    __check_key(key)
    __check_index(index)

    key_handle = __resolve_key(key)
    try:
        sub_key_str = list(key_handle.handle.subkeys.keys())[index]
        return sub_key_str
    except IndexError:
        error = OSError("[WinError 259] No more data is available")
        setattr(error, "winerror", 259)
        raise error


@check_for_kwargs_wrapt
# EnumValue{{{
def EnumValue(key: Handle, index: int) -> Tuple[str, RegData, int]:  # noqa
    """
    Enumerates values of an open registry key, returning a tuple.
    The function retrieves the name of one value each time it is called.
    It is typically called repeatedly, until an OSError exception is raised, indicating no more values.
    the function does NOT accept named parameters, only positional parameters



    Parameter
    ---------

    key:
        an already open key, or one of the predefined HKEY_* constants.

    index:
        an integer that identifies the index of the key to retrieve.



    Result
    ------

    The result is a tuple of 3 items:

    ========    ==============================================================================================
    Index       Meaning
    ========    ==============================================================================================
    0           A string that identifies the value name
    1           An object that holds the value data, and whose type depends on the underlying registry type
    2           An integer giving the registry type for this value (see table in docs for SetValueEx())
    ========    ==============================================================================================



    Exceptions
    ----------

    OSError: [WinError 259] No more data is available
        if the index is out of Range

    OSError: [WinError 6] The handle is invalid
        if parameter key is invalid

    TypeError: None is not a valid HKEY in this context
        if parameter key is None

    TypeError: The object is not a PyHKEY object
        if parameter key is not integer or PyHKEY type

    OverflowError: int too big to convert
        if parameter key is > 64 Bit Integer Value

    TypeError: an integer is required (got type <type>)
        if parameter index is type different from int

    OverflowError: Python int too large to convert to C int
        if parameter index is > 64 Bit Integer Value

    TypeError: EnumValue() got some positional-only arguments passed as keyword arguments: '<key>'
        if a keyword (named) parameter was passed



    Events
    ------

    Raises an auditing event winreg.EnumValue with arguments key, index. (NOT IMPLEMENTED)



    Registry Types
    --------------

    ==============  ==============================  ==============================  ==========================================================================
    type(int)       type name                       accepted python Types           Description
    ==============  ==============================  ==============================  ==========================================================================
    0               REG_NONE	                     None, bytes                     No defined value type.
    1               REG_SZ	                        None, str                       A null-terminated string.
    2               REG_EXPAND_SZ	                None, str                       Null-terminated string containing references to
                                                                                    environment variables (%PATH%).
                                                                                    (Python handles this termination automatically.)
    3               REG_BINARY	                    None, bytes                     Binary data in any form.
    4               REG_DWORD	                    None, int                       A 32-bit number.
    4               REG_DWORD_LITTLE_ENDIAN	        None, int                       A 32-bit number in little-endian format.
    5               REG_DWORD_BIG_ENDIAN	        None, bytes                     A 32-bit number in big-endian format.
    6               REG_LINK	                    None, bytes                     A Unicode symbolic link.
    7               REG_MULTI_SZ	                None, List[str]                 A sequence of null-terminated strings, terminated by two null characters.
    8               REG_RESOURCE_LIST	            None, bytes                     A device-driver resource list.
    9               REG_FULL_RESOURCE_DESCRIPTOR    None, bytes                     A hardware setting.
    10              REG_RESOURCE_REQUIREMENTS_LIST  None, bytes                     A hardware resource list.
    11              REG_QWORD                       None, bytes                     A 64 - bit number.
    11              REG_QWORD_LITTLE_ENDIAN         None, bytes                     A 64 - bit number in little - endian format.Equivalent to REG_QWORD.
    ==============  ==============================  ==============================  ==========================================================================

    * all other integers for REG_TYPE are accepted, and written to the registry. The value is handled as binary.
    by that way You would be able to encode data in the REG_TYPE for stealth data not easy to spot - who would expect it.



    Examples
    --------

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
    # EnumValue}}}

    __check_key(key)
    __check_index(index)

    key_handle = __resolve_key(key)
    try:
        value_name = list(key_handle.handle.values.keys())[index]
        value_data = key_handle.handle.values[value_name].value
        value_type = key_handle.handle.values[value_name].value_type
        return value_name, value_data, value_type
    except IndexError:
        error = OSError("[WinError 259] No more data is available")
        setattr(error, "winerror", 259)
        raise error


# named arguments are allowed here !
# OpenKey{{{
def OpenKey(key: Handle, sub_key: Union[str, None], reserved: int = 0, access: int = KEY_READ) -> PyHKEY:  # noqa
    """
    Opens the specified key, the result is a new handle to the specified key.
    one of the few functions of winreg that accepts named parameters



    Parameter
    ---------

    key:
        an already open key, or one of the predefined HKEY_* constants.

    sub_key:
        None, or a string that names the key this method opens or creates.
        If key is one of the predefined keys, sub_key may be None.

    reserved:
        reserved is a reserved integer, and should be zero. The default is zero.

    access:
        a integer that specifies an access mask that describes the desired security access for the key.
        Default is KEY_READ. See Access Rights for other allowed values.
        (any integer is accepted here in original winreg, bit masked against KEY_* access parameters)



    Exceptions
    ----------

    OSError: ...
        if it fails to open the key

    OSError: [WinError 6] The handle is invalid
        if parameter key is invalid

    TypeError: None is not a valid HKEY in this context
        if parameter key is None

    TypeError: The object is not a PyHKEY object
        if parameter key is not integer or PyHKEY type

    OverflowError: int too big to convert
        if parameter key is > 64 Bit Integer Value

    TypeError: OpenKey() argument 2 must be str or None, not <type>
        if the sub_key is anything else then str or None

    TypeError: an integer is required (got NoneType)
        if parameter reserved is None

    TypeError: an integer is required (got type <type>)
        if parameter reserved is not int

    PermissionError: [WinError 5] Access denied
        if parameter reserved is > 3)

    OverflowError: Python int too large to convert to C long
        if parameter reserved is > 64 Bit Integer Value

    OSError: [WinError 87] The parameter is incorrect
        on some values for reserved (for instance 455565) NOT IMPLEMENTED

    TypeError: an integer is required (got type <type>)
        if parameter access is not int

    OverflowError: Python int too large to convert to C long
        if parameter access is > 64 Bit Integer Value



    Events
    ------

    Raises an auditing event winreg.OpenKey with arguments key, sub_key, access.    # not implemented
    Raises an auditing event winreg.OpenKey/result with argument key.               # not implemented



    Examples
    --------

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)

    >>> # Open Key
    >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
    >>> assert key_handle.handle.full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'

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
    # OpenKey}}}

    __check_key(key)
    __check_argument_must_be_str_or_none(arg_number=2, argument=sub_key)
    __check_reserved2(reserved)
    __check_access(access)

    if sub_key is None:
        sub_key = ""

    try:
        key_handle = __resolve_key(key)
        reg_key = fake_reg.get_fake_reg_key(key_handle.handle, sub_key=sub_key)
        key_handle = PyHKEY(reg_key, access=access)
        return key_handle
    except FileNotFoundError:
        error = FileNotFoundError("[WinError 2] The system cannot find the file specified")
        setattr(error, "winerror", 2)
        raise error


# named arguments are allowed here !
# OpenKeyEx{{{
def OpenKeyEx(key: Handle, sub_key: Optional[str], reserved: int = 0, access: int = KEY_READ) -> PyHKEY:  # noqa
    """
    Opens the specified key, the result is a new handle to the specified key with the given access.
    one of the few functions of winreg that accepts named parameters



    Parameter
    ---------

    key:
        an already open key, or one of the predefined HKEY_* constants.

    sub_key:
        None, or a string that names the key this method opens or creates.
        If key is one of the predefined keys, sub_key may be None.

    reserved:
        reserved is a reserved integer, and should be zero. The default is zero.

    access:
        a integer that specifies an access mask that describes the desired security access for the key.
        Default is KEY_READ. See Access Rights for other allowed values.
        (any integer is accepted here in original winreg, bit masked against KEY_* access parameters)



    Exceptions
    ----------

    OSError: ...
        if it fails to open the key

    OSError: [WinError 6] The handle is invalid
        if parameter key is invalid

    TypeError: None is not a valid HKEY in this context
        if parameter key is None

    TypeError: The object is not a PyHKEY object
        if parameter key is not integer or PyHKEY type

    OverflowError: int too big to convert
        if parameter key is > 64 Bit Integer Value

    TypeError: OpenKeyEx() argument 2 must be str or None, not <type>
        if the subkey is anything else then str or None

    TypeError: an integer is required (got NoneType)
        if parameter reserved is None

    TypeError: an integer is required (got type <type>)
        if parameter reserved is not int

    PermissionError: [WinError 5] Access denied
        if parameter reserved is > 3)

    OverflowError: Python int too large to convert to C long
        if parameter reserved is > 64 Bit Integer Value

    OSError: [WinError 87] The parameter is incorrect
        on some values for reserved (for instance 455565) NOT IMPLEMENTED

    TypeError: an integer is required (got type <type>)
        if parameter access is not int

    OverflowError: Python int too large to convert to C long
        if parameter access is > 64 Bit Integer Value



    Events
    ------

    Raises an auditing event winreg.OpenKey with arguments key, sub_key, access.    # not implemented
    Raises an auditing event winreg.OpenKey/result with argument key.               # not implemented



    Examples
    --------

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)

    >>> # Open Key
    >>> my_key_handle = OpenKeyEx(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
    >>> assert my_key_handle.handle.full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'

    >>> # Open Key with Context Manager
    >>> with OpenKeyEx(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion') as my_key_handle:
    ...     assert my_key_handle.handle.full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'

    >>> # Open non existing Key
    >>> OpenKeyEx(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\DoesNotExist')
    Traceback (most recent call last):
        ...
    FileNotFoundError: [WinError 2] The system cannot find the file specified

    """
    # OpenKeyEx}}}

    key_handle = OpenKey(key, sub_key, reserved, access)
    return key_handle


@check_for_kwargs_wrapt
# QueryInfoKey{{{
def QueryInfoKey(key: Handle) -> Tuple[int, int, int]:  # noqa
    """
    Returns information about a key, as a tuple.
    the function does NOT accept named parameters, only positional parameters



    Parameter
    ---------

    key:
        the predefined handle to connect to, or one of the predefined HKEY_* constants.



    Result
    ------

    The result is a tuple of 3 items:

    ======  =============================================================================================================
    Index,  Meaning
    ======  =============================================================================================================
    0       An integer giving the number of sub keys this key has.
    1       An integer giving the number of values this key has.
    2       An integer giving when the key was last modified (if available) as 100’s of nanoseconds since Jan 1, 1601.
    ======  =============================================================================================================



    Exceptions
    ----------

    OSError: [WinError 6] The handle is invalid
        if parameter key is invalid

    TypeError: None is not a valid HKEY in this context
        if parameter key is None

    TypeError: The object is not a PyHKEY object
        if parameter key is not integer or PyHKEY type

    OverflowError: int too big to convert
        if parameter key is > 64 Bit Integer Value

    TypeError: QueryInfoKey() got some positional-only arguments passed as keyword arguments: '<key>'
        if a keyword (named) parameter was passed



    Events
    ------

    Raises an auditing event winreg.QueryInfoKey with argument key.



    Examples and Tests:
    -------------------


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
    # QueryInfoKey}}}

    __check_key(key)
    reg_handle = __resolve_key(key)
    n_subkeys = len(reg_handle.handle.subkeys)
    n_values = len(reg_handle.handle.values)
    last_modified_nanoseconds = reg_handle.handle.last_modified_ns  # 100’s of nanoseconds since Jan 1, 1601. / 1.Jan.1970 diff = 11644473600 * 1E9
    return n_subkeys, n_values, last_modified_nanoseconds


@check_for_kwargs_wrapt
# QueryValue{{{
def QueryValue(key: Handle, sub_key: Union[str, None]) -> str:  # noqa
    """
    Retrieves the unnamed value (the default value*) for a key, as string.

    * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)"
    it is usually not set. Nethertheless, even if the value is not set, QueryValue will deliver ''

    Values in the registry have name, type, and data components.

    This method retrieves the data for a key’s first value that has a NULL name.
    But the underlying API call doesn’t return the type, so always use QueryValueEx() if possible.

    the function does NOT accept named parameters, only positional parameters


    Parameter
    ---------

    key:
        the predefined handle to connect to, or one of the predefined HKEY_* constants.

    sub_key:
        None, or a string that names the key this method opens or creates.
        If key is one of the predefined keys, sub_key may be None. In that case,
        the handle returned is the same key handle passed in to the function.
        If the key already exists, this function opens the existing key.



    Result
    ------

    the unnamed value as string (if possible)



    Exceptions
    ----------

    OSError: [WinError 13] The data is invalid
        if the data in the unnamed value is not string

    OSError: [WinError 6] The handle is invalid
        if parameter key is invalid

    TypeError: None is not a valid HKEY in this context
        if parameter key is None

    TypeError: The object is not a PyHKEY object
        if parameter key is not integer or PyHKEY type

    OverflowError: int too big to convert
        if parameter key is > 64 Bit Integer Value

    TypeError: QueryValue() argument 2 must be str or None, not <type>
        if the subkey is anything else then str or None

    TypeError: QueryValue() got some positional-only arguments passed as keyword arguments: '<key>'
        if a keyword (named) parameter was passed



    Events:
    -------

    Raises an auditing event winreg.QueryValue with arguments key, sub_key, value_name. (NOT IMPLEMENTED)



    Examples
    --------

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
    >>> assert QueryValueEx(key_handle_created, '') == ('test1', REG_SZ)
    >>> assert QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == 'test1'

    >>> # set the default value to non-string type, and try to get it with Query Value
    >>> SetValueEx(key_handle_created, '', 0, REG_DWORD, 42)
    >>> assert QueryValueEx(key_handle_created, '') == (42, REG_DWORD)
    >>> QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test')
    Traceback (most recent call last):
        ...
    OSError: [WinError 13] The data is invalid

    >>> # Teardown
    >>> DeleteKey(reg_handle, r'SOFTWARE\\lib_registry_test')

    """
    # QueryValue}}}

    __check_key(key)
    __check_argument_must_be_str_or_none(arg_number=2, argument=sub_key)

    key_handle = __resolve_key(key)
    key_handle = OpenKey(key_handle, sub_key)
    try:
        result = key_handle.handle.values[""].value
        if not isinstance(result, str):
            error = OSError("[WinError 13] The data is invalid")
            setattr(error, "winerror", 13)
            raise error
        isinstance(result, str)
        default_value = result
    except KeyError:
        default_value = ""

    return default_value


@check_for_kwargs_wrapt
# QueryValueEx{{{
def QueryValueEx(key: Handle, value_name: Optional[str]) -> Tuple[RegData, int]:  # noqa
    """
    Retrieves data and type for a specified value name associated with an open registry key.

    If Value_name is '' or None, it queries the Default Value* of the Key - this will Fail if the Default Value for the Key is not Present.
    * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)"
    it is usually not set.

    the function does NOT accept named parameters, only positional parameters



    Parameter
    ---------

    key:
        the predefined handle to connect to, or one of the predefined HKEY_* constants.

    value_name:
        None, or a string that identifies the value to Query
        if value is None, or '' it queries the default Value of the Key



    Result
    ------

    The result is a tuple of 2 items:

    ==========  =====================================================================================================
    Index       Meaning
    ==========  =====================================================================================================
    0           The value of the registry item.
    1           An integer giving the registry type for this value see table
    ==========  =====================================================================================================



    Registry Types
    --------------

    ==============  ==============================  ==============================  ==========================================================================
    type(int)       type name                       accepted python Types           Description
    ==============  ==============================  ==============================  ==========================================================================
    0               REG_NONE	                    None, bytes                     No defined value type.
    1               REG_SZ	                        None, str                       A null-terminated string.
    2               REG_EXPAND_SZ	                None, str                       Null-terminated string containing references to
                                                                                    environment variables (%PATH%).
                                                                                    (Python handles this termination automatically.)
    3               REG_BINARY	                    None, bytes                     Binary data in any form.
    4               REG_DWORD	                    None, int                       A 32-bit number.
    4               REG_DWORD_LITTLE_ENDIAN	        None, int                       A 32-bit number in little-endian format.
    5               REG_DWORD_BIG_ENDIAN	        None, bytes                     A 32-bit number in big-endian format.
    6               REG_LINK	                    None, bytes                     A Unicode symbolic link.
    7               REG_MULTI_SZ	                None, List[str]                 A sequence of null-terminated strings, terminated by two null characters.
    8               REG_RESOURCE_LIST	            None, bytes                     A device-driver resource list.
    9               REG_FULL_RESOURCE_DESCRIPTOR    None, bytes                     A hardware setting.
    10              REG_RESOURCE_REQUIREMENTS_LIST  None, bytes                     A hardware resource list.
    11              REG_QWORD                       None, bytes                     A 64 - bit number.
    11              REG_QWORD_LITTLE_ENDIAN         None, bytes                     A 64 - bit number in little - endian format.Equivalent to REG_QWORD.
    ==============  ==============================  ==============================  ==========================================================================

    * all other integers for REG_TYPE are accepted, and written to the registry. The value is handled as binary.
    by that way You would be able to encode data in the REG_TYPE for stealth data not easy to spot - who would expect it.



    Exceptions
    ----------

    OSError: [WinError 6] The handle is invalid
        if parameter key is invalid

    TypeError: None is not a valid HKEY in this context
        if parameter key is None

    TypeError: The object is not a PyHKEY object
        if parameter key is not integer or PyHKEY type

    OverflowError: int too big to convert
        if parameter key is > 64 Bit Integer Value

    TypeError: QueryValueEx() argument 2 must be str or None, not <type>
        if the value_name is anything else then str or None

    TypeError: QueryValueEx() got some positional-only arguments passed as keyword arguments: '<key>'
        if a keyword (named) parameter was passed



    Events
    ------

    Raises an auditing event winreg.QueryValue with arguments key, sub_key, value_name. (NOT Implemented)



    Examples
    --------

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
    # QueryValueEx}}}

    __check_key(key)
    __check_argument_must_be_str_or_none(arg_number=2, argument=value_name)

    try:
        if value_name is None:
            value_name = ""
        key_handle = __resolve_key(key)
        value = key_handle.handle.values[value_name].value
        value_type = key_handle.handle.values[value_name].value_type
        return value, value_type
    except KeyError:
        error = FileNotFoundError("[WinError 2] The system cannot find the file specified")
        setattr(error, "winerror", 2)
        raise error


@check_for_kwargs_wrapt
# SetValue{{{
def SetValue(key: Handle, sub_key: Union[str, None], type: int, value: str) -> None:  # noqa
    """
    Associates a value with a specified key. (the Default Value* of the Key, usually not set)

    * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)"
    it is usually not set. Nethertheless, even if the value is not set, QueryValue will deliver ''

    the function does NOT accept named parameters, only positional parameters


    Parameter
    ---------

    key:
        the predefined handle to connect to, or one of the predefined HKEY_* constants.

    sub_key:
        None, or a string that names the key this method sets the default value
        If the key specified by the sub_key parameter does not exist, the SetValue function creates it.

    type:
        an integer that specifies the type of the data. Currently this must be REG_SZ,
        meaning only strings are supported. Use the SetValueEx() function for support for other data types.

    value:
        a string that specifies the new value.
        Value lengths are limited by available memory. Long values (more than 2048 bytes) should be stored
        as files with the filenames stored in the configuration registry. This helps the registry perform efficiently.
        The key identified by the key parameter must have been opened with KEY_SET_VALUE access.    (NOT IMPLEMENTED)



    Exceptions
    ----------

    TypeError: Could not convert the data to the specified type.
        for REG_SZ and REG_EXPAND_SZ, if the data is not NoneType or str,
        for REG_DWORD and REG_EXPREG_QWORDAND_SZ, if the data is not NoneType or int,
        for REG_MULTI_SZ, if the data is not List[str]:

    TypeError: Objects of type '<data_type>' can not be used as binary registry values
        for all other REG_* types, if the data is not NoneType or bytes

    OSError: [WinError 6] The handle is invalid
        if parameter key is invalid

    TypeError: None is not a valid HKEY in this context
        if parameter key is None

    TypeError: The object is not a PyHKEY object
        if parameter key is not integer or PyHKEY type

    OverflowError: int too big to convert
        if parameter key is > 64 Bit Integer Value

    TypeError: SetValue() argument 2 must be str or None, not <type>
        if the subkey is anything else then str or None

    TypeError: SetValue() argument 3 must be int not None
        if the type is None

    TypeError: SetValue() argument 3 must be int not <type>
        if the type is anything else but int

    TypeError: type must be winreg.REG_SZ
        if the type is not string (winreg.REG_SZ)

    TypeError: SetValue() argument 4 must be str not None
        if the value is None

    TypeError: SetValue() argument 4 must be str not <type>
        if the value is anything else but str

    TypeError: SetValue() got some positional-only arguments passed as keyword arguments: '<key>'
        if a keyword (named) parameter was passed



    Events
    ------

    Raises an auditing event winreg.SetValue with arguments key, sub_key, type, value. (NOT IMPLEMENTED)



    Examples
    --------

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

    >>> # SetValue creates keys on the fly if they do not exist
    >>> reg_handle_software = OpenKey(reg_handle, 'SOFTWARE')
    >>> SetValue(reg_handle_software, r'lib_registry_test\\ham\\spam', REG_SZ, 'wonderful spam')
    >>> assert QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test\\ham\\spam') == 'wonderful spam'

    >>> # You can not use other types as string here
    >>> SetValue(key_handle, '', REG_DWORD, "42")     # noqa
    Traceback (most recent call last):
        ...
    TypeError: type must be winreg.REG_SZ

    >>> # Tear Down
    >>> DeleteKey(reg_handle,r'SOFTWARE\\lib_registry_test\\ham\\spam')
    >>> DeleteKey(reg_handle,r'SOFTWARE\\lib_registry_test\\ham')
    >>> DeleteKey(reg_handle,r'SOFTWARE\\lib_registry_test')

    """
    # SetValue}}}

    __check_key(key)
    __check_argument_must_be_str_or_none(arg_number=2, argument=sub_key)
    __check_argument_must_be_type_expected(arg_number=3, argument=type, type_expected=int)
    __check_argument_must_be_type_expected(arg_number=4, argument=value, type_expected=str)

    if type != REG_SZ:
        # checked - like winreg
        raise TypeError("type must be winreg.REG_SZ")

    key_handle = __resolve_key(key)
    access = key_handle._access
    try:
        # create the key if not there
        key_handle = OpenKey(key_handle, sub_key, 0, access=access)
    except FileNotFoundError:
        key_handle = CreateKey(key_handle, sub_key)
    SetValueEx(key_handle, "", 0, REG_SZ, value)


@check_for_kwargs_wrapt
# SetValueEx{{{
def SetValueEx(key: Handle, value_name: Optional[str], reserved: int, type: int, value: RegData) -> None:  # noqa
    """
    Stores data in the value field of an open registry key.

    value_name is a string that names the subkey with which the value is associated.
    if value is None, or '' it sets the default value* of the Key

    the function does NOT accept named parameters, only positional parameters

    Parameter
    ---------

    key:
        the predefined handle to connect to, or one of the predefined HKEY_* constants.
        The key identified by the key parameter must have been opened with KEY_SET_VALUE access.    (NOT IMPLEMENTED))
        To open the key, use the CreateKey() or OpenKey() methods.

    value_name:
        None, or a string that identifies the value to set
        if value is None, or '' it sets the default value* of the Key

        * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)"
        it is usually not set, but You can set it to any data and datatype - but then it will
        only be readable with QueryValueEX, not with QueryValue

    reserved:
        reserved is a reserved integer, and should be zero. reserved can be anything – zero is always passed to the API.

    type:
        type is an integer that specifies the type of the data. (see table)

    value:
        value is a new value.
        Value lengths are limited by available memory. Long values (more than 2048 bytes)
        should be stored as files with the filenames stored in the configuration registry. This helps the registry perform efficiently.


    Registry Types

    ==============  ==============================  ==============================  ==========================================================================
    type(int)       type name                       accepted python Types           Description
    ==============  ==============================  ==============================  ==========================================================================
    0               REG_NONE	                    None, bytes                     No defined value type.
    1               REG_SZ	                        None, str                       A null-terminated string.
    2               REG_EXPAND_SZ	                None, str                       Null-terminated string containing references to
                                                                                    environment variables (%PATH%).
                                                                                    (Python handles this termination automatically.)
    3               REG_BINARY	                    None, bytes                     Binary data in any form.
    4               REG_DWORD	                    None, int                       A 32-bit number.
    4               REG_DWORD_LITTLE_ENDIAN	        None, int                       A 32-bit number in little-endian format.
    5               REG_DWORD_BIG_ENDIAN	        None, bytes                     A 32-bit number in big-endian format.
    6               REG_LINK	                    None, bytes                     A Unicode symbolic link.
    7               REG_MULTI_SZ	                None, List[str]                 A sequence of null-terminated strings, terminated by two null characters.
    8               REG_RESOURCE_LIST	            None, bytes                     A device-driver resource list.
    9               REG_FULL_RESOURCE_DESCRIPTOR    None, bytes                     A hardware setting.
    10              REG_RESOURCE_REQUIREMENTS_LIST  None, bytes                     A hardware resource list.
    11              REG_QWORD                       None, bytes                     A 64 - bit number.
    11              REG_QWORD_LITTLE_ENDIAN         None, bytes                     A 64 - bit number in little - endian format.Equivalent to REG_QWORD.
    ==============  ==============================  ==============================  ==========================================================================

    * all other integers for REG_TYPE are accepted, and written to the registry. The value is handled as binary.
    by that way You would be able to encode data in the REG_TYPE for stealth data not easy to spot - who would expect it.



    Exceptions
    ----------

    OSError: [WinError 6] The handle is invalid
        if parameter key is invalid

    TypeError: None is not a valid HKEY in this context
        if parameter key is None

    TypeError: The object is not a PyHKEY object
        if parameter key is not integer or PyHKEY type

    OverflowError: int too big to convert
        if parameter key is > 64 Bit Integer Value

    TypeError: SetValueEx() argument 2 must be str or None, not <type>
        if the value_name is anything else then str or None

    TypeError: SetValueEx() argument 4 must be int not None
        if the type is None

    TypeError: SetValueEx() argument 4 must be int not <type>
        if the type is anything else but int

    TypeError: SetValueEx() got some positional-only arguments passed as keyword arguments: '<key>'
        if a keyword (named) parameter was passed



    Events
    ------

    Raises an auditing event winreg.SetValue with arguments key, sub_key, type, value.          (NOT IMPLEMENTED)



    Examples
    --------

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)
    >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)
    >>> key_handle = CreateKey(reg_handle, r'Software\\lib_registry_test')

    >>> # Test
    >>> SetValueEx(key_handle, 'some_test', 0, REG_SZ, 'some_test_value')
    >>> assert QueryValueEx(key_handle, 'some_test') == ('some_test_value', REG_SZ)

    >>> # Test Overwrite
    >>> SetValueEx(key_handle, 'some_test', 0, REG_SZ, 'some_test_value2')
    >>> assert QueryValueEx(key_handle, 'some_test') == ('some_test_value2', REG_SZ)

    >>> # Test write Default Value of the Key, with value_name None
    >>> SetValueEx(key_handle, None, 0, REG_SZ, 'default_value')
    >>> assert QueryValue(key_handle, '') == 'default_value'

    >>> # Test write Default Value of the Key, with value_name ''
    >>> SetValueEx(key_handle, '', 0, REG_SZ, 'default_value_overwritten')
    >>> assert QueryValue(key_handle, '') == 'default_value_overwritten'

    >>> # Teardown
    >>> DeleteValue(key_handle, 'some_test')
    >>> DeleteKey(key_handle, '')

    """
    # SetValueEx}}}

    __check_key(key)
    __check_argument_must_be_str_or_none(arg_number=2, argument=value_name)
    # parameter 3 can be anything, it is ignored
    __check_argument_must_be_type_expected(arg_number=4, argument=type, type_expected=int)

    # value name = None is the default Value of the Key
    if value_name is None:
        value_name = ""
    fake_reg_tools.__check_value_type_matches_type(value, type)
    key_handle = __resolve_key(key)
    fake_reg.set_fake_reg_value(key_handle.handle, sub_key="", value_name=value_name, value=value, value_type=type)


def __resolve_key(key: Handle) -> PyHKEY:
    """
    Returns the full path to the key

    >>> # Setup
    >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
    >>> load_fake_registry(fake_registry)

    >>> # Connect registry and get PyHkey Type
    >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)

    >>> __resolve_key(key=reg_handle).handle.full_key
    'HKEY_CURRENT_USER'

    >>> __resolve_key(key=HKEY_CURRENT_USER).handle.full_key
    'HKEY_CURRENT_USER'

    >>> # Test PyHKey Type (the most common)
    >>> discard = __resolve_key(reg_handle)

    >>> # Test int Type
    >>> discard = __resolve_key(HKEY_CURRENT_USER)

    >>> # Test HKEYType
    >>> hkey = HKEYType(handle=reg_handle.handle, access=reg_handle._access)
    >>> discard = __resolve_key(hkey)

    >>> # Test invalid handle
    >>> discard = __resolve_key(42)
    Traceback (most recent call last):
        ...
    OSError: [WinError 6] The handle is invalid

    >>> # Test invalid type
    >>> discard = __resolve_key('spam')  # noqa
    Traceback (most recent call last):
        ...
    RuntimeError: unknown Key Type

    """

    if isinstance(key, PyHKEY):
        key_handle = key
    elif isinstance(key, int):
        try:
            key_handle = PyHKEY(__fake_registry.hive[key])
        except KeyError:
            error = OSError("[WinError 6] The handle is invalid")
            setattr(error, "winerror", 6)
            raise error
    elif isinstance(key, HKEYType):
        key_handle = PyHKEY(handle=key.handle, access=key._access)
    else:
        raise RuntimeError("unknown Key Type")
    return key_handle


def __check_argument_must_be_type_expected(arg_number: int, argument: Any, type_expected: type) -> None:
    """
    >>> __check_argument_must_be_type_expected(arg_number=2, argument=None, type_expected=int)
    Traceback (most recent call last):
        ...
    TypeError: ...() argument 2 must be int, not None

    >>> __check_argument_must_be_type_expected(arg_number=2, argument='spam', type_expected=int)
    Traceback (most recent call last):
        ...
    TypeError: ...() argument 2 must be int, not str

    >>> __check_argument_must_be_type_expected(arg_number=2, argument='spam', type_expected=str)

    """
    function_name = inspect.stack()[1].function
    if not isinstance(argument, type_expected):
        argument_type = type(argument).__name__
        if argument_type == "NoneType":
            argument_type = "None"
        error_str = "{function_name}() argument {arg_number} must be {type_expected}, not {argument_type}".format(
            function_name=function_name,
            arg_number=arg_number,
            type_expected=type_expected.__name__,
            argument_type=argument_type,
        )
        raise TypeError(error_str)


def __check_argument_must_be_str_or_none(arg_number: int, argument: Any) -> None:
    function_name = inspect.stack()[1].function
    if not isinstance(argument, str) and argument is not None:
        subkey_type = type(argument).__name__
        error_str = f"{function_name}() argument {arg_number} must be str or None, not {subkey_type}"
        raise TypeError(error_str)


def __check_key(key: Any) -> None:
    if key is None:
        raise TypeError("None is not a valid HKEY in this context")
    if not isinstance(key, int) and not isinstance(key, PyHKEY):
        raise TypeError("The object is not a PyHKEY object")
    if isinstance(key, int):
        if key >= 2**64:
            raise OverflowError("int too big to convert")


def __check_index(index: Any) -> None:
    """
    >>> __check_index(1)

    >>> __check_index(2 ** 64)
    Traceback (most recent call last):
        ...
    OverflowError: Python int too large to convert to C long

    >>> __check_index('spam')
    Traceback (most recent call last):
        ...
    TypeError: an integer is required (got type str)

    >>> __check_index(None)
    Traceback (most recent call last):
        ...
    TypeError: an integer is required (got type NoneType)

    """

    index_type = type(index).__name__
    if not isinstance(index, int):
        raise TypeError("an integer is required (got type {access_type})".format(access_type=index_type))
    elif index >= 2**64:
        raise OverflowError("Python int too large to convert to C long")


def __check_access(access: Any) -> None:
    __check_index(access)  # same as __check_index


def __check_reserved(reserved: Any) -> None:
    """
    >>> __check_reserved(0)
    >>> __check_reserved(1)
    Traceback (most recent call last):
        ...
    OSError: [WinError 87] The parameter is incorrect
    """
    __check_access(reserved)  # same as access
    if isinstance(reserved, int) and reserved != 0:
        error = OSError("[WinError 87] The parameter is incorrect")
        setattr(error, "winerror", 87)
        raise error


def __check_reserved2(reserved: Any) -> None:
    """
    >>> __check_reserved2(0)
    >>> __check_reserved2(4)
    Traceback (most recent call last):
        ...
    PermissionError: [WinError 5] Access is denied

    >>> __check_reserved2(2 ** 64)
    Traceback (most recent call last):
        ...
    OverflowError: Python int too large to convert to C long

    >>> __check_reserved2('spam')
    Traceback (most recent call last):
        ...
    TypeError: an integer is required (got type str)

    """
    if isinstance(reserved, int):
        if 3 < reserved < 2**64:
            __raise_permission_error()
    __check_access(reserved)  # otherwise same as __check_access


def __raise_permission_error() -> None:
    permission_error = PermissionError("[WinError 5] Access is denied")
    setattr(permission_error, "winerror", 5)
    raise permission_error


def __raise_os_error_1010() -> None:
    error = OSError("[WinError 1010] The configuration registry key is invalid")
    setattr(error, "winerror", 1010)
    raise error
