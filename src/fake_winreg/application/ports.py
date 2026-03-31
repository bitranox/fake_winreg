"""Application ports — callable Protocol definitions for adapter functions.

Each Protocol class defines a ``__call__`` method whose signature exactly
matches the corresponding adapter function.  Existing module-level functions
satisfy these protocols automatically via structural subtyping (PEP 544).

System Role:
    Sits between domain and adapters.  Infrastructure types (``Config``,
    ``EmailConfig``) are imported under ``TYPE_CHECKING`` only so that
    import-linter layer contracts remain satisfied at runtime.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from ..domain.enums import DeployTarget, OutputFormat
from ..domain.registry import FakeRegistryKey, FakeRegistryValue
from ..domain.types import RegData

if TYPE_CHECKING:
    from lib_layered_config import Config

    from ..adapters.email.sender import EmailConfig


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
        set_permissions: bool = ...,
        dir_mode: int | None = ...,
        file_mode: int | None = ...,
    ) -> list[Path]: ...


class DisplayConfig(Protocol):
    """Display the provided configuration in the requested format."""

    def __call__(
        self, config: Config, *, output_format: OutputFormat = ..., section: str | None = ..., profile: str | None = ...
    ) -> None: ...


class SendEmail(Protocol):
    """Send an email using configured SMTP settings."""

    def __call__(
        self,
        *,
        config: EmailConfig,
        recipients: str | Sequence[str] | None = ...,
        subject: str,
        body: str = ...,
        body_html: str = ...,
        from_address: str | None = ...,
        attachments: Sequence[Path] | None = ...,
    ) -> bool: ...


class SendNotification(Protocol):
    """Send a simple plain-text notification email."""

    def __call__(
        self,
        *,
        config: EmailConfig,
        recipients: str | Sequence[str] | None = ...,
        subject: str,
        message: str,
        from_address: str | None = ...,
    ) -> bool: ...


class LoadEmailConfigFromDict(Protocol):
    """Load EmailConfig from a configuration dictionary."""

    def __call__(self, config_dict: Mapping[str, Any]) -> EmailConfig: ...


class InitLogging(Protocol):
    """Initialize lib_log_rich runtime with the provided configuration."""

    def __call__(self, config: Config) -> None: ...


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

    def enum_values(self, key: FakeRegistryKey) -> list[tuple[str, RegData, int]]:
        """List values as (name, data, type) tuples."""
        ...

    def query_info(self, key: FakeRegistryKey) -> tuple[int, int, int]:
        """Return (num_subkeys, num_values, last_modified_ns)."""
        ...


__all__ = [
    "DeployConfiguration",
    "DisplayConfig",
    "GetConfig",
    "GetDefaultConfigPath",
    "InitLogging",
    "LoadEmailConfigFromDict",
    "SendEmail",
    "SendNotification",
    "NetworkResolver",
    "RegistryBackend",
]
