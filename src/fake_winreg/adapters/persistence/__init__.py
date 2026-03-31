"""Registry persistence adapters — backends and import/export functions."""

from __future__ import annotations

from fake_winreg.domain.memory_backend import InMemoryBackend

from .json_backend import JsonBackend
from .json_io import export_json, import_json
from .reg_io import export_reg, import_reg
from .sqlite_backend import SqliteBackend

__all__ = [
    "InMemoryBackend",
    "JsonBackend",
    "SqliteBackend",
    "export_json",
    "export_reg",
    "import_json",
    "import_reg",
]
