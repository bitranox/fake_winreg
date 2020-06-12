from typing import Tuple, Union

# to avoid Import Error on Linux and make it possible to have hints when develop in linux


class PyHKEY(object):
    HKEY_CLASSES_ROOT: int = 18446744071562067968
    HKEY_CURRENT_CONFIG: int = 18446744071562067973
    HKEY_CURRENT_USER: int = 18446744071562067969
    HKEY_DYN_DATA: int = 18446744071562067974
    HKEY_LOCAL_MACHINE: int = 18446744071562067970
    HKEY_PERFORMANCE_DATA: int = 18446744071562067972
    HKEY_USERS: int = 18446744071562067971


class WinRegFake(object):
    handle: int = 0
    REG_SZ: int = 1
    KEY_READ: int = 131097
    KEY_WRITE: int = 131078
    KEY_ALL_ACCESS: int = 983103
    HKEYType: PyHKEY = PyHKEY
    HKEY_CLASSES_ROOT: PyHKEY = PyHKEY.HKEY_CLASSES_ROOT
    HKEY_CURRENT_CONFIG: PyHKEY = PyHKEY.HKEY_CURRENT_CONFIG
    HKEY_CURRENT_USER: PyHKEY = PyHKEY.HKEY_CURRENT_USER
    HKEY_DYN_DATA: PyHKEY = PyHKEY.HKEY_DYN_DATA
    HKEY_LOCAL_MACHINE: PyHKEY = PyHKEY.HKEY_LOCAL_MACHINE
    HKEY_PERFORMANCE_DATA: PyHKEY = PyHKEY.HKEY_PERFORMANCE_DATA
    HKEY_USERS: PyHKEY = PyHKEY

    @staticmethod
    def QueryInfoKey(key: HKEYType) -> Tuple[int, int, int]:
        return 0, 0, 0

    @classmethod
    def CloseKey(cls, hkey: handle):
        return cls.handle

    @classmethod
    def ConnectRegistry(cls, computer_name: Union[None, str], key: HKEYType) -> handle:
        return cls.handle

    @classmethod
    def CreateKey(cls, key: HKEYType, sub_key: str) -> handle:
        return cls.handle

    @ staticmethod
    def DeleteKey(key: HKEYType, sub_key: str) -> None:
        pass

    @staticmethod
    def DeleteValue(key: HKEYType, value: str) -> None:
        pass

    @staticmethod
    def EnumKey(key: HKEYType, index: int) -> str:
        return ''

    @classmethod
    def OpenKey(cls, key: HKEYType, sub_key: str, res: int = 0, sam: int = KEY_READ) -> handle:
        return cls.handle

    @staticmethod
    def SetValueEx(key: HKEYType, value_name: str, reserved: int, type: int, value: str):
        pass

    @staticmethod
    def QueryValueEx(key: HKEYType, value_name: str) -> Tuple[str, int]:
        return '', 0
