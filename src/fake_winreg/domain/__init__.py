"""Domain layer - pure business logic with no I/O or framework dependencies.

Contains the fake Windows registry implementation: data structures, handles,
constants, API functions, and validation logic.

Contents:
    * :mod:`.types` - Registry value data types
    * :mod:`.constants` - Windows registry constants (HKEY_*, REG_*, KEY_*)
    * :mod:`.registry` - Core data structures (FakeRegistry, FakeRegistryKey, FakeRegistryValue)
    * :mod:`.handles` - Handle types (HKEYType, PyHKEY)
    * :mod:`.api` - Winreg-compatible API functions
    * :mod:`.helpers` - String manipulation helpers
    * :mod:`.validation` - Value type validation
    * :mod:`.test_registries` - Pre-built test registry builders
    * :mod:`.enums` - Domain enumerations (OutputFormat, DeployTarget)
    * :mod:`.errors` - Domain exception types
"""

from __future__ import annotations

from .enums import DeployTarget, OutputFormat
from .errors import ConfigurationError

__all__ = [
    # Enums
    "DeployTarget",
    "OutputFormat",
    # Errors
    "ConfigurationError",
]
