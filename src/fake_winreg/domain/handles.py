"""Registry handle types wrapping fake registry keys.

Provides HKEYType and PyHKEY (context manager) that mirror the Windows
winreg handle objects, plus thread-safe handle ID generation.
"""

from __future__ import annotations

import threading
from types import TracebackType

from .constants import KEY_READ
from .registry import FakeRegistryKey

# Handle counter starts around 600 like real winreg
_last_int_handle: int = 600
_last_int_handle_lock = threading.Lock()


class HKEYType:
    """Base registry handle wrapping a FakeRegistryKey.

    >>> hkey = HKEYType(handle=FakeRegistryKey())
    >>> assert int(hkey) != 0
    """

    def __init__(self, handle: FakeRegistryKey, access: int = KEY_READ) -> None:
        self.handle = handle
        self._access = access
        global _last_int_handle
        with _last_int_handle_lock:
            _last_int_handle += 1
            self._int_handle = _last_int_handle

    def __int__(self) -> int:
        return self._int_handle

    def __bool__(self) -> bool:
        return True

    def __eq__(self, other: object) -> bool:
        if isinstance(other, HKEYType):
            return self._int_handle == other._int_handle
        if isinstance(other, int):
            return self._int_handle == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._int_handle)

    @staticmethod
    def Close() -> None:  # noqa: N802
        """Close the underlying handle (no-op in fake implementation)."""

    @staticmethod
    def Detach() -> int:  # noqa: N802
        """Detach the handle, returning 0 (no-op in fake implementation)."""
        return 0


class PyHKEY(HKEYType):
    """Registry handle with context manager support.

    >>> p = PyHKEY(FakeRegistryKey())
    >>> p.Close()
    >>> assert p.Detach() == 0
    """

    def __init__(self, handle: FakeRegistryKey, access: int = KEY_READ) -> None:
        super().__init__(handle, access)

    def __enter__(self) -> PyHKEY:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.Close()


Handle = int | HKEYType | PyHKEY
"""The possible types of a handle that can be passed to winreg functions."""

__all__ = [
    "HKEYType",
    "Handle",
    "PyHKEY",
]
