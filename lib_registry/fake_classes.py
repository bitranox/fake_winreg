from typing import Tuple, Union, Type

# to avoid Import Error on Linux and make it possible to have hints when develop in linux


class PyHKEY(object):
    pass


class handle(object):
    pass


class WinRegFake(object):
    REG_SZ: int = 1
    KEY_READ: int = 131097
    KEY_WRITE: int = 131078
    KEY_ALL_ACCESS: int = 983103
    HKEYType = PyHKEY
    HKEY_CLASSES_ROOT: int = 18446744071562067968
    HKEY_CURRENT_CONFIG: int = 18446744071562067973
    HKEY_CURRENT_USER: int = 18446744071562067969
    HKEY_DYN_DATA: int = 18446744071562067974
    HKEY_LOCAL_MACHINE: int = 18446744071562067970
    HKEY_PERFORMANCE_DATA: int = 18446744071562067972
    HKEY_USERS: int = 18446744071562067971

    @staticmethod
    def QueryInfoKey(key: PyHKEY) -> Tuple[int, int, int]:
        n_subkeys = 0
        n_values = 0
        last_modified_nanoseconds = 0       # 100’s of nanoseconds since Jan 1, 1601.
        return n_subkeys, n_values, last_modified_nanoseconds

    @staticmethod
    def CloseKey(hkey: PyHKEY):
        return handle()

    @staticmethod
    def ConnectRegistry(computer_name: Union[None, str], key: PyHKEY) -> PyHKEY:
        handle = PyHKEY()
        return handle

    @staticmethod
    def CreateKey(key: PyHKEY, sub_key: str) -> PyHKEY:
        handle = PyHKEY()
        return handle

    @ staticmethod
    def DeleteKey(key: PyHKEY, sub_key: str) -> None:
        pass

    @staticmethod
    def DeleteValue(key: PyHKEY, value: str) -> None:
        pass

    @staticmethod
    def EnumKey(key: PyHKEY, index: int) -> str:
        return ''

    @staticmethod
    def OpenKey(key: PyHKEY, sub_key: str, res: int = 0, sam: int = KEY_READ) -> PyHKEY:
        handle = PyHKEY()
        return handle

    @staticmethod
    def SetValueEx(key: PyHKEY, value_name: str, reserved: int, type: int, value: str):
        pass

    @staticmethod
    def QueryValueEx(key: PyHKEY, value_name: str) -> Tuple[str, PyHKEY]:
        handle = PyHKEY()
        return '', handle
