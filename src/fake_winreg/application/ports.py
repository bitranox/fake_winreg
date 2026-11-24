"""Application ports - callable Protocol definitions for adapter functions.

Each Protocol class defines a ``__call__`` method whose signature exactly
matches the corresponding adapter function.  Existing module-level functions
satisfy these protocols automatically via structural subtyping (PEP 544).

System Role:
    Sits between domain and adapters.  Infrastructure types (``Config``)
    are imported under ``TYPE_CHECKING`` only so that import-linter layer
    contracts remain satisfied at runtime.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from lib_layered_config import Config

    from ..domain.enums import DeployTarget, OutputFormat
    from ..domain.registry import FakeRegistryKey, FakeRegistryValue
    from ..domain.types import KeyInfo, RegData, ValueEntry


class GetConfig(Protocol):
    """Load layered configuration with application defaults."""

    def __call__(
        self, *, profile: str | None = ..., start_dir: str | None = ..., dotenv_path: str | None = ...
    ) -> Config: ...


class GetDefaultConfigPath(Protocol):
    """Return the path to the bundled default configuration file."""

    def __call__(self) -> Path: ...


class DeployConfiguration(Protocol):
    """Deploy default configuration to specified target layers."""

    def __call__(
        self,
        *,
        targets: Sequence[DeployTarget],
        force: bool = ...,
        profile: str | None = ...,
        set_permissions: bool | None = ...,
        dir_mode: int | None = ...,
        file_mode: int | None = ...,
        permission_overrides: Mapping[str, object] | None = ...,
    ) -> list[Path]: ...


class DisplayConfig(Protocol):
    """Display the provided configuration in the requested format."""

    def __call__(
        self, config: Config, *, output_format: OutputFormat = ..., section: str | None = ..., profile: str | None = ...
    ) -> None: ...


class InitLogging(Protocol):
    """Initialize lib_log_rich runtime with the provided configuration.

    ``dotenv_path`` is the ``.env`` the configuration was loaded with, or None for the nearest one.
    A refused logging setting raises ``InvalidLoggingConfigError`` only after logging has been
    started with its defaults, so the caller never has to start it a second time.
    """

    def __call__(self, config: Config, *, dotenv_path: str | None = None) -> None: ...


class NetworkResolver(Protocol):
    """Check whether a computer name can be resolved on the network."""

    def __call__(self, computer_name: str, /) -> bool: ...


class RegistryBackend(Protocol):
    """Storage backend for fake registry keys and values.

    Implementations: InMemoryBackend, SqliteBackend, JsonBackend.
    """

    def get_hive(self, hive_key: int) -> FakeRegistryKey:
        """Return the root key for a predefined HKEY_* constant."""
        ...

    def get_key(self, base_key: FakeRegistryKey, sub_key: str) -> FakeRegistryKey:
        """Retrieve an existing key. Raises FileNotFoundError if missing."""
        ...

    def create_key(self, base_key: FakeRegistryKey, sub_key: str | None) -> FakeRegistryKey:
        """Create a key (and intermediate parents). Returns the key."""
        ...

    def delete_key(self, base_key: FakeRegistryKey, sub_key: str) -> None:
        """Delete a leaf key. Raises PermissionError if it has subkeys."""
        ...

    def get_value(self, key: FakeRegistryKey, value_name: str) -> FakeRegistryValue:
        """Retrieve a value. Raises KeyError if missing."""
        ...

    def set_value(self, key: FakeRegistryKey, value_name: str, value: RegData, value_type: int) -> None:
        """Create or update a value."""
        ...

    def delete_value(self, key: FakeRegistryKey, value_name: str) -> None:
        """Delete a value. Raises KeyError if missing."""
        ...

    def enum_keys(self, key: FakeRegistryKey) -> list[str]:
        """List subkey names."""
        ...

    def enum_values(self, key: FakeRegistryKey) -> list[ValueEntry]:
        """List the values of a key."""
        ...

    def subkey_name_at(self, key: FakeRegistryKey, index: int) -> str:
        """Return the name of the subkey at *index*, in ``enum_keys`` order.

        ``EnumKey`` calls this once per index while a caller walks a key, so an
        implementation must not rebuild the whole name list per call.  A
        negative *index* counts from the end (list indexing), as it did when
        ``EnumKey`` indexed ``enum_keys()`` directly.

        Raises:
            IndexError: If *index* is out of range (``EnumKey`` turns this into
                WinError 259, "No more data is available").
        """
        ...

    def value_at(self, key: FakeRegistryKey, index: int) -> ValueEntry:
        """Return the value at *index*, in ``enum_values`` order.

        Same cost and indexing contract as :meth:`subkey_name_at`.

        Raises:
            IndexError: If *index* is out of range.
        """
        ...

    def query_info(self, key: FakeRegistryKey) -> KeyInfo:
        """Return the subkey count, value count and last-modified time of a key."""
        ...


__all__ = [
    "DeployConfiguration",
    "DisplayConfig",
    "GetConfig",
    "GetDefaultConfigPath",
    "InitLogging",
    "NetworkResolver",
    "RegistryBackend",
]
