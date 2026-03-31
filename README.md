# fake_winreg

<!-- Badges -->
[![CI](https://github.com/bitranox/fake_winreg/actions/workflows/default_cicd_public.yml/badge.svg)](https://github.com/bitranox/fake_winreg/actions/workflows/default_cicd_public.yml)
[![CodeQL](https://github.com/bitranox/fake_winreg/actions/workflows/codeql.yml/badge.svg)](https://github.com/bitranox/fake_winreg/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Open in Codespaces](https://img.shields.io/badge/Codespaces-Open-blue?logo=github&logoColor=white&style=flat-square)](https://codespaces.new/bitranox/fake_winreg?quickstart=1)
[![PyPI](https://img.shields.io/pypi/v/fake_winreg.svg)](https://pypi.org/project/fake_winreg/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/fake_winreg.svg)](https://pypi.org/project/fake_winreg/)
[![Code Style: Ruff](https://img.shields.io/badge/Code%20Style-Ruff-46A3FF?logo=ruff&labelColor=000)](https://docs.astral.sh/ruff/)
[![codecov](https://codecov.io/gh/bitranox/fake_winreg/graph/badge.svg?token=UFBaUDIgRk)](https://codecov.io/gh/bitranox/fake_winreg)
[![Maintainability](https://qlty.sh/badges/041ba2c1-37d6-40bb-85a0-ec5a8a0aca0c/maintainability.svg)](https://qlty.sh/gh/bitranox/projects/fake_winreg)
[![Known Vulnerabilities](https://snyk.io/test/github/bitranox/fake_winreg/badge.svg)](https://snyk.io/test/github/bitranox/fake_winreg)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
  - [Registry Functions](#registry-functions)
  - [Backend Management](#backend-management)
  - [Import / Export](#import--export)
  - [Constants](#constants)
  - [Data Types](#data-types)
  - [Test Registries](#test-registries)
- [CLI Usage](#cli-usage)
- [Development](#development)
- [License](#license)

## Overview

`fake_winreg` provides a drop-in replacement for Python's built-in
[`winreg`](https://docs.python.org/3/library/winreg.html) module, enabling
testing of Windows registry-dependent code on Linux and macOS without a
Windows environment.

**Key capabilities:**

- All 20 `winreg` API functions (`OpenKey`, `SetValueEx`, `EnumKey`, etc.) with matching signatures and error behavior
- Three storage backends: **in-memory** (default), **SQLite** (for large registries), **JSON** (for fixtures)
- Import and export of Windows `.reg` files (Registry Editor Version 5.00 format)
- Streaming format conversion between `.db`, `.json`, and `.reg` via CLI or Python API
- Pre-built test registries mimicking Windows 10 and Wine environments
- Positional-only parameter enforcement matching real `winreg` behavior
- Clean Architecture with `import-linter` enforcement, pyright strict mode, 92% test coverage

## Installation

### Recommended: uv (fast, isolated)

```bash
# install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# one-shot run without installing
uvx fake_winreg@latest info

# persistent install as CLI tool
uv tool install fake_winreg

# install as project dependency
uv pip install fake_winreg
```

### Via pip

```bash
pip install fake_winreg
```

### From source

```bash
pip install "git+https://github.com/bitranox/fake_winreg"
```

See [INSTALL.md](INSTALL.md) for all options (pipx, Poetry, PDM, system packages).

## Quick Start

```python
import fake_winreg as winreg

# Load a pre-built Windows 10-like test registry
fake_registry = winreg.fake_reg_tools.get_minimal_windows_testregistry()
winreg.load_fake_registry(fake_registry)

# Use exactly like the real winreg module
reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
key = winreg.OpenKey(reg, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
value, value_type = winreg.QueryValueEx(key, "CurrentBuild")
```

## API Reference

All functions mirror the signatures and behavior of Python's built-in `winreg` module.

### Registry Functions

#### Connection

```python
ConnectRegistry(computer_name: str | None, key: Handle, /) -> PyHKEY
```

Establish a connection to a predefined registry handle. Pass `None` for `computer_name` to connect to the local (fake) registry.

#### Key Operations

```python
CreateKey(key: Handle, sub_key: str | None, /) -> PyHKEY
```

Create or open a registry key, returning a handle.

```python
CreateKeyEx(key: Handle, sub_key: str, reserved: int = 0, access: int = KEY_WRITE, /) -> PyHKEY
```

Create or open a registry key with explicit access control.

```python
OpenKey(key: Handle, sub_key: str | None, reserved: int = 0, access: int = KEY_READ) -> PyHKEY
```

Open an existing registry key. Does not create the key if it does not exist.

```python
OpenKeyEx(key: Handle, sub_key: str | None, reserved: int = 0, access: int = KEY_READ) -> PyHKEY
```

Open an existing registry key with explicit access. Equivalent to `OpenKey`.

```python
DeleteKey(key: Handle, sub_key: str, /) -> None
```

Delete a registry key. The key must have no subkeys.

```python
DeleteKeyEx(key: Handle, sub_key: str, access: int = KEY_WOW64_64KEY, reserved: int = 0, /) -> None
```

Delete a registry key (64-bit variant).

```python
CloseKey(hkey: int | HKEYType, /) -> None
```

Close a previously opened registry key.

```python
FlushKey(key: Handle, /) -> None
```

Write all attributes of a key to the registry. No-op in the fake implementation since data is already in memory.

#### Value Operations

```python
SetValue(key: Handle, sub_key: str | None, type: int, value: str, /) -> None
```

Set the default (unnamed) value of a key. Only `REG_SZ` is accepted for `type`.

```python
SetValueEx(key: Handle, value_name: str | None, reserved: int, type: int, value: RegData, /) -> None
```

Store data in a named value of an open registry key. Supports all registry value types.

```python
QueryValue(key: Handle, sub_key: str | None, /) -> str
```

Retrieve the default (unnamed) value of a key as a string.

```python
QueryValueEx(key: Handle, value_name: str | None, /) -> tuple[RegData, int]
```

Retrieve value data and its type code for a named value. Returns `(data, type)`.

```python
DeleteValue(key: Handle, value: str | None, /) -> None
```

Remove a named value from a registry key.

#### Enumeration

```python
EnumKey(key: Handle, index: int, /) -> str
```

Enumerate subkeys of an open key by zero-based index. Raises `OSError` when `index` exceeds the number of subkeys.

```python
EnumValue(key: Handle, index: int, /) -> tuple[str, RegData, int]
```

Enumerate values of an open key by zero-based index. Returns `(name, data, type)`. Raises `OSError` when `index` exceeds the number of values.

```python
QueryInfoKey(key: Handle, /) -> tuple[int, int, int]
```

Return information about a key: `(num_subkeys, num_values, last_modified_timestamp)`.

#### Utility

```python
ExpandEnvironmentStrings(string: str, /) -> str
```

Expand `%VAR%`-style environment variable references in a string. Works on all platforms.

```python
DisableReflectionKey(key: Handle, /) -> None
EnableReflectionKey(key: Handle, /) -> None
QueryReflectionKey(key: Handle, /) -> bool
```

Registry reflection stubs. No-op in the fake implementation; `QueryReflectionKey` always returns `True`.

### Backend Management

`fake_winreg` supports multiple storage backends. The default is an in-memory backend.

```python
import fake_winreg as winreg

# Default: in-memory (created automatically if no backend is set)
winreg.use_backend(winreg.InMemoryBackend())

# SQLite: for large registries or persistent storage
winreg.use_backend(winreg.SqliteBackend("/path/to/registry.db"))

# JSON: load from a JSON file, work in memory
winreg.use_backend(winreg.JsonBackend("/path/to/registry.json"))

# Backward-compatible: load a FakeRegistry object directly
fake_registry = winreg.fake_reg_tools.get_minimal_windows_testregistry()
winreg.load_fake_registry(fake_registry)
```

### Import/Export

Exchange registry data between formats.

```python
import fake_winreg as winreg

# JSON format
winreg.export_json("/path/to/snapshot.json")
winreg.import_json("/path/to/fixture.json")

# Windows .reg format
winreg.export_reg("/path/to/export.reg")
winreg.import_reg("/path/to/import.reg")

# Convert between formats
winreg.convert_registry("source.db", "target.reg")
```

### Constants

All constants from the `winreg` module are available.

**Hive keys:**

| Constant               | Description                                      |
|------------------------|--------------------------------------------------|
| `HKEY_CLASSES_ROOT`    | Registry entries for file associations and COM    |
| `HKEY_CURRENT_USER`    | Settings for the current user                     |
| `HKEY_LOCAL_MACHINE`   | System-wide settings                              |
| `HKEY_USERS`           | Settings for all user profiles                    |
| `HKEY_CURRENT_CONFIG`  | Current hardware profile                          |
| `HKEY_PERFORMANCE_DATA` | Performance counters                             |
| `HKEY_DYN_DATA`        | Dynamic data (Windows 95/98)                      |

**Value types:**

| Constant                          | Description                                          |
|-----------------------------------|------------------------------------------------------|
| `REG_NONE`                        | No defined value type                                |
| `REG_SZ`                          | Null-terminated string                               |
| `REG_EXPAND_SZ`                   | String with unexpanded environment variable refs     |
| `REG_BINARY`                      | Binary data                                          |
| `REG_DWORD`                       | 32-bit integer (little-endian)                       |
| `REG_DWORD_BIG_ENDIAN`            | 32-bit integer (big-endian)                          |
| `REG_LINK`                        | Symbolic link (Unicode)                              |
| `REG_MULTI_SZ`                    | Array of null-terminated strings                     |
| `REG_QWORD`                       | 64-bit integer (little-endian)                       |
| `REG_RESOURCE_LIST`               | Device driver resource list                          |
| `REG_FULL_RESOURCE_DESCRIPTOR`    | Hardware resource descriptor                         |
| `REG_RESOURCE_REQUIREMENTS_LIST`  | Hardware resource requirements                       |

**Access rights:**

| Constant                | Description                            |
|-------------------------|----------------------------------------|
| `KEY_READ`              | Read access                            |
| `KEY_WRITE`             | Write access                           |
| `KEY_ALL_ACCESS`        | Full access                            |
| `KEY_EXECUTE`           | Execute access (same as `KEY_READ`)    |
| `KEY_QUERY_VALUE`       | Query subkey values                    |
| `KEY_SET_VALUE`         | Set subkey values                      |
| `KEY_CREATE_SUB_KEY`    | Create subkeys                         |
| `KEY_ENUMERATE_SUB_KEYS` | Enumerate subkeys                     |
| `KEY_NOTIFY`            | Change notification                    |
| `KEY_CREATE_LINK`       | Create symbolic link                   |
| `KEY_WOW64_64KEY` | Access 64-bit registry view |
| `KEY_WOW64_32KEY` | Access 32-bit registry view |

### Data Types

```python
# All possible types of data that registry values can hold
RegData = None | bytes | int | str | list[str]

# Handle types accepted by all API functions
Handle = int | HKEYType | PyHKEY

# Registry data structures
FakeRegistry       # Top-level registry container (holds hive roots)
FakeRegistryKey    # A single registry key with subkeys and values
FakeRegistryValue  # A named value with data and type code
```

`PyHKEY` supports the context manager protocol:

```python
with winreg.OpenKey(reg, r"SOFTWARE\Microsoft") as key:
    value, vtype = winreg.QueryValueEx(key, "SomeName")
```

### Test Registries

Pre-built registry fixtures for common test scenarios.

```python
import fake_winreg as winreg

# Pre-built Windows 10-like registry with typical keys under
# HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion
reg = winreg.fake_reg_tools.get_minimal_windows_testregistry()

# Pre-built Wine-like registry
reg = winreg.fake_reg_tools.get_minimal_wine_testregistry()
```

## CLI Usage

```bash
# Convert between registry formats
fake-winreg convert if=registry.db of=export.reg
fake-winreg convert if=export.reg of=registry.json

# Show package information
fake-winreg info
```

## Development

Run the full test suite (lint, type-check, tests with coverage):

```bash
make test
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for the complete development setup guide.

## License

[MIT](LICENSE)
