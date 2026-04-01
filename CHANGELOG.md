# Changelog

All notable changes to this project will be documented in this file following
the [Keep a Changelog](https://keepachangelog.com/) format.


## [Unreleased]

## [1.8.2] - 2026-04-01

### Changed
- README: clarified that fake_winreg also supports testing without hitting a real registry on Windows

## [1.8.1] - 2026-03-31

### Changed
- README: added "Why fake_winreg?" section, real-world .reg import workflow,
  updated feature list with REGEDIT4, Windows 11, reg CLI, current coverage

## [1.8.0] - 2026-03-31

### Added
- `reg` CLI command group with 8 subcommands for persistent SQLite registry operations:
  list-keys, list-values, get, set, create-key, delete-key, delete-value, info
- `export-demo-registries` CLI command generating Windows 10, 11, and Wine fixtures
- Windows 11 23H2 Pro test registry (`get_minimal_windows11_testregistry`)
- REGEDIT4 (version 4) .reg export support via `export_reg(path, version=4)`
- UTF-16 LE with BOM as default .reg export encoding (matching Windows regedit.exe)
- Auto-detection of .reg file encoding on import (UTF-16 LE BOM or UTF-8)
- `registry.db_path` configuration via TOML config, .env, or environment variables
- 25 end-to-end format tests with full 9-pair conversion matrix
- `docs/registry_values.md` — Windows registry values reference with version detection guide

### Fixed
- `EnumKey`/`EnumValue` now return insertion order (matching real winreg), sorted only in exports
- .reg export escapes `\n` and `\r` in string values
- .reg hex line continuation uses `\r\n` consistently with file encoding
- `.reg → .json` conversion uses InMemoryBackend instead of unnecessary temp SQLite
- `FakeRegistryValue.value` defaults to `None` instead of `""`
- `HKEYType` implements `__bool__`, `__eq__`, `__hash__` for handle comparison and dict usage
- Windows 11 test registry UBR corrected to real value 4317 (KB5044285)
- .reg export writes bytes directly to avoid Windows text-mode `\r\n` double-escaping

### Changed
- Removed email subsystem (adapters, CLI commands, tests, config)
- README: added Configuration section, CLI quick start, REGEDIT4 docs, charset table

## [1.7.0] - 2026-03-31

### Added
- Integrated the full fake Windows registry implementation into clean architecture scaffold
- All 20 winreg-compatible API functions: ConnectRegistry, OpenKey, CreateKey, SetValueEx, EnumKey, QueryInfoKey, etc.
- 6 additional winreg functions: FlushKey, ExpandEnvironmentStrings, DisableReflectionKey, EnableReflectionKey, QueryReflectionKey, error
- RegistryBackend Protocol with three implementations:
  - InMemoryBackend (default, backward-compatible)
  - SqliteBackend (live DB for large registries)
  - JsonBackend (load-into-memory on open)
- Import/export for JSON and Windows .reg file formats (import_json, export_json, import_reg, export_reg)
- Streaming format conversion: convert_registry() Python API and `fake-winreg convert if=... of=...` CLI command
- Pre-built test registries: get_minimal_windows_testregistry(), get_minimal_wine_testregistry()
- TypedDicts for serialization format (RegistryDict, KeyDict, ValueDict, Base64Marker)
- Domain layer: registry data structures, handles, constants, types, validation, helpers, serialization
- Network adapter for DNS-based computer reachability (injected via composition)
- CLI convert command with dd-style syntax

### Changed
- Replaced wrapt dependency with Python 3.10+ positional-only parameter syntax (/)
- Replaced inspect.stack() with sys._getframe() in validators (47% faster test suite)
- Compiled regex pattern at module level in ExpandEnvironmentStrings
- All exports produce deterministic, alphabetically sorted output across all backends
- Updated all documentation: README with full API reference and TOC, pyproject.toml keywords, CONFIG.md, notebooks
- Project description updated to "A fake Windows registry for testing registry-related code on non-Windows platforms"

### Removed
- Placeholder greeting code (build_greeting, cli_hello, cli_fail, behaviors.py)
- wrapt dependency

## [1.5.3] - 2026-03-30

### Changed
- Bumped Codecov GitHub Action to V6
- Updated CVE exclusion list: removed stale entries, added inline documentation for remaining exclusions
- pip-audit set to warning-only to reduce CI noise

### Fixed
- Email transport: minor improvements to SMTP handling

## [1.5.2] - 2026-03-05

### Fixed
- Re-release as 1.5.2: PyPI rejected 1.5.1 due to filename reuse after prior upload deletion

### Changed
- `get_permission_defaults()` now returns a `PermissionDefaults` Pydantic model instead of a raw dict, with typed field access and `dir_mode_for()`/`file_mode_for()` methods
- `EmailSpy` now stores captured calls as `CapturedEmail` and `CapturedNotification` frozen dataclasses instead of `list[dict[str, Any]]`

### Added
- Tests for `--env-file` CLI option (argument passing, validation, end-to-end integration)

## [1.5.1] - 2026-03-05 [YANKED]

### Changed
- `get_permission_defaults()` now returns a `PermissionDefaults` Pydantic model instead of a raw dict, with typed field access and `dir_mode_for()`/`file_mode_for()` methods
- `EmailSpy` now stores captured calls as `CapturedEmail` and `CapturedNotification` frozen dataclasses instead of `list[dict[str, Any]]`

### Added
- Tests for `--env-file` CLI option (argument passing, validation, end-to-end integration)

## [1.5.0] - 2026-03-02

### Added
- `--env-file PATH` global CLI option to load an explicit `.env` file instead of searching upward from the working directory
- `dotenv_path` parameter added to `GetConfig` protocol, config loader, and in-memory adapter
- `__all__` to `__init__conf__.py` listing all public symbols
- `@pytest.mark.integration` marker on email integration tests

### Fixed
- Subprocess tests (`test_module_entry_subprocess_help`, `test_module_entry_subprocess_version`) now pass without editable install by setting `PYTHONPATH` to `src/`
- pip-audit CVE-2025-8869 ignore (pip is environment-level, not a project dependency)

### Changed
- CI workflow: dynamic Python version matrix extracted from `pyproject.toml` classifiers
- CI workflow: ruff cache restricted to GitHub-hosted runners
- CI workflow: bandit reads configuration from `pyproject.toml` (`-c pyproject.toml`)
- CI workflow: Codecov upload uses dynamically resolved latest Python version
- Release workflow: `actions/upload-artifact` upgraded to v7
- Added `[tool.hatch.metadata]` and `[tool.bashate]` sections to `pyproject.toml`
- Documentation updates: CONFIG.md, README.md, DEVELOPMENT.md for `--env-file` option

## [1.4.1] - 2026-02-13

### Fixed
- `reset_git_history.sh`: fixed shellcheck SC1083 warning by quoting `HEAD^{tree}` and normalized indentation to 4 spaces (shfmt)

### Changed
- Updated Makefile from v2.2.1 to v2.3.3
- Bumped dependency minimums: `lib_cli_exit_tools` >=2.3.0, `lib_log_rich` >=6.3.3, `lib_layered_config` >=5.4.1
- Added CVE ignore entries for CVE-2026-26007 and CVE-2026-25990
- Updated CI/CD workflows and added Bash 4+ requirement for macOS

## [1.4.0] - 2026-02-13

### Changed
- **Build automation**: replaced `scripts/` directory with `bmk`-based Makefile (`uvx bmk@latest`); all build, test, bump, push, and release tasks now delegated to `bmk`
- Makefile updated to v2.2.1 with alias targets, trailing argument forwarding, and new commands (config, email, info, logdemo)

## [1.3.1] - 2026-02-13

### Fixed
- `tests/test_metadata_sync.py`: replaced `importlib.metadata` lookups with direct `pyproject.toml` reads — tests no longer fail when the package is not installed in the test environment (uvx)
- Makefile `dev` target now correctly installs dev extras (`uv pip install -e ".[dev]"`)

### Changed
- CLAUDE.md: updated project structure trees to reflect actual codebase (added `entry.py`, `domain/errors.py`, `adapters/memory/`, `adapters/config/permissions.py`, `adapters/email/validation.py`; removed deleted `traceback.py`)
- CLAUDE.md: rewrote Make targets table to match new `bmk`-based Makefile (added aliases, new targets; removed obsolete `menu`, `test-slow`)
- CLAUDE.md: corrected versioning documentation — runtime metadata is served from `__init__conf__.py` constants, not `importlib.metadata`
- CLAUDE.md: replaced stale `scripts/` instrumentation section with `bmk` delegation note
- CLAUDE.md: updated `make test-slow` references to `make testintegration`

## [1.3.0] - 2026-02-01

### Added
- **File permission options for `config-deploy`**: `--permissions/--no-permissions`, `--dir-mode`, `--file-mode`
- **Configurable permission defaults** in `[lib_layered_config.default_permissions]` (app/host: 755/644, user: 700/600)
- **Octal string support** in config files (`"0o755"`, `"755"`, or decimal `493`)

### Changed
- `deploy_configuration()` accepts `set_permissions`, `dir_mode`, `file_mode` parameters
- CONFIG.md: comprehensive CLI options reference, `sudo -u` deployment examples

## [1.2.1] - 2026-02-01

### Changed
- **Profile validation** now delegates to `lib_layered_config.validate_profile_name()` with comprehensive security checks:
  - Maximum length enforcement (64 characters)
  - Empty string rejection
  - Windows reserved name rejection (CON, PRN, AUX, NUL, COM1-9, LPT1-9)
  - Leading character validation (must start with alphanumeric)
  - Path traversal prevention (/, \, ..)
- `validate_profile()` now accepts optional `max_length` parameter for customization

### Added
- `40-layered-config.toml` in `defaultconfig.d/` documenting lib_layered_config integration settings
- Profile validation tests for length limits, empty strings, Windows reserved names, and leading character rules
- Profile name requirements documentation in CONFIG.md and README.md

### Removed
- Custom `_PROFILE_PATTERN` regex — replaced by lib_layered_config's built-in validation

## [1.2.0] - 2026-01-30

### Added
- **Attachment security settings** for email configuration (`[email.attachments]` section in `50-mail.toml`)
  - `allowed_extensions` / `blocked_extensions` — whitelist/blacklist file extensions
  - `allowed_directories` / `blocked_directories` — whitelist/blacklist attachment source directories
  - `max_size_bytes` — maximum attachment file size (default 25 MiB, 0 to disable)
  - `allow_symlinks` — whether symbolic links are permitted (default false)
  - `raise_on_security_violation` — raise or skip on violations (default true)
- New `EmailConfig` fields for attachment security with Pydantic validators
- `load_email_config_from_dict()` now flattens nested `[email.attachments]` section

### Changed
- Bumped `btx_lib_mail` dependency from `>=1.2.1` to `>=1.3.0` for attachment security features

## [1.1.2] - 2026-01-28

### Fixed
- Coverage SQLite "database is locked" errors on Python 3.14 free-threaded builds and network mounts (SMB/NFS)
- Removed bogus `COVERAGE_NO_SQL=1` environment variable from `scripts/test.py` (not a real coverage.py setting)
- CI workflow now sets `COVERAGE_FILE` to `runner.temp` so coverage always writes to local disk
- **Import-linter was a silent no-op** in `make test` / `make push` — `python -m importlinter.cli lint` silently exits 0 without checking; replaced with `lint-imports` (the working console entry point)
- CI/local parameter mismatches: ruff now targets `.` (not hardcoded `src tests notebooks`), pytest uses `python -m pytest` with `--cov=src/$PACKAGE_MODULE`, `--cov-fail-under=90`, and `-vv` matching local runs
- `scripts/test.py` bandit source path now reads `src-path` from `[tool.scripts.test]` instead of hardcoding `Path("src")`
- `scripts/test.py` module-level `_default_env` now rebuilt with configured `src_path` before running checks
- `run_slow_tests()` now reads pytest verbosity from `[tool.scripts.test].pytest-verbosity` instead of hardcoding `"-vv"`

### Changed
- **pyproject.toml as single source of truth**: CI workflow extracts all tool configuration (src-path, pytest-verbosity, coverage-report-file, fail_under, bandit skips) from `pyproject.toml` via metadata step — workflow is portable across projects without editing
- `scripts/test.py` removed module-level `PACKAGE_SRC` constant; bandit source path computed from `config.src_path` inside the functions that need it
- `make push` now accepts an unquoted message as trailing words (e.g. `make push fix typo in readme`); commit message format is `<version> - <message>`, defaulting to `<version> - chores` when no message is given
- Removed interactive commit-message prompt from `push.py` — message is either provided via CLI args / `COMMIT_MESSAGE` env var, or defaults to `"chores"`

### Added
- `pytest_configure` hook in `tests/conftest.py` that redirects coverage data to `tempfile.gettempdir()` and purges stale SQLite journal files before each run

## [1.1.1] - 2026-01-28

### Fixed
- CLAUDE.md: replaced stale package name `bitranox_template_cli_app_config_log_mail` with `fake_winreg` throughout
- Brittle SMTP mock assertions in `test_cli.py` now use structured `call_args` attributes instead of `str()` coercion
- Stale docstring in `__init__conf__.py` claiming "adapters/platform layer" — corrected to "Package-level metadata module"
- Weak OR assertion in `test_cli.py` for SMTP host display — replaced with two independent assertions
- Removed stale `# type: ignore[reportUnknownVariableType]` from `sender.py` (`btx_lib_mail.ConfMail` now has proper type annotations)
- Late function-body imports in `adapters/cli/commands/config.py` moved to module-level for consistency

### Removed
- Dead code: unused `_format_value()` and `_format_source()` wrappers in `adapters/config/display.py`

### Added
- `__all__` to `__init__conf__.py` listing all public symbols
- `tests/test_enums.py` with parametrized tests for `OutputFormat` and `DeployTarget`
- Expanded `tests/test_behaviors.py` with return type, constant value, and constant-usage checks
- Python 3.14 classifier in `pyproject.toml`
- Codecov upload step in CI workflow (gated to `ubuntu-latest` + `3.13`)
- Edge-case tests for `parse_override`: bare `=value`, bare `=`, and CLI `--set ""` empty string
- Duplication-tracking comments for CI metadata extraction scripts

### Changed
- `tests/test_display.py` rewritten to test `_format_raw_value` and `_format_source_line` directly (replacing dead wrapper tests)

## [1.1.0] - 2026-01-27

### Changed
- Replaced `MockConfig` in-memory adapter with real `Config` objects in all tests (`config_factory` / `inject_config` fixtures)
- Replaced `MagicMock` Config objects in CLI email tests with real `Config` instances
- Unified test names to BDD-style `test_when_<condition>_<behavior>` pattern in `test_cli.py`
- Email integration tests now load configuration via `lib_layered_config` instead of dedicated `TEST_SMTP_SERVER` / `TEST_EMAIL_ADDRESS` environment variables

### Added
- Cache effectiveness tests for `get_config()` and `get_default_config_path()` LRU caches (`tests/test_cache_effectiveness.py`)
- Callable Protocol definitions in `application/ports.py` for all adapter functions, with static conformance assertions and `tests/test_ports.py`
- `ExitCode` IntEnum (`adapters/cli/exit_codes.py`) with POSIX-conventional exit codes for all CLI error paths
- `logdemo` and `config-generate-examples` CLI commands
- `--set SECTION.KEY=VALUE` repeatable CLI option for runtime configuration overrides (`adapters.config.overrides` module)
- Unit tests for config overrides and display module (sensitive key matching, redaction, nested rendering)

### Removed
- Dead code: `raise_intentional_failure()`, `noop_main()`, `cli_main()`, duplicate `cli_session` orchestration, catch-log-reraise in `send_email()`
- Replaced dead `ConfigPort`/`EmailPort` protocol classes with callable Protocol definitions

### Fixed
- POSIX-conventional exit codes across all CLI error paths (replacing hardcoded `SystemExit(1)`)
- Sensitive value redaction: word-boundary matching to avoid false positives, nested dict/list redaction, TOML sub-section rendering
- Email validation: reject bogus addresses (`@`, `user@`, `@domain`); IPv6 SMTP host support; credential construction
- Profile name validation against path traversal
- Security: list-based subprocess calls in scripts, sensitive env-var redaction in test output, stale CVE exclusion cleanup
- Documentation: wrong project name references, truncated CLI command names, stale import paths, wrong layer descriptions
- CI: `actions/download-artifact` version mismatch, stale `codecov.yml` ignore patterns
- Unified `__main__.py` and `adapters/cli/main.py` error handling via delegation

### Changed
- Precompile all regex patterns in `scripts/` as module-level constants for consistent compilation
- **LIBRARIES**: Replace custom redaction/validation with `lib_layered_config` redaction API and `btx_lib_mail` validators; bump both libraries
- **LIBRARIES**: Replace stdlib `json` with `orjson`; replace `urllib` with `httpx` in scripts
- **ARCHITECTURE**: Purified domain layer — `emit_greeting()` renamed to `build_greeting()` (returns `str`, no I/O); decoupled `display.py` from Click
- **DATA ARCHITECTURE**: Consolidated `EmailConfig` into single Pydantic `BaseModel` (eliminated dataclass conversion chain)

## [1.0.0] - 2026-01-15

### Added
- Slow integration test infrastructure (`make test-slow`, `@pytest.mark.slow` marker)
- `pydantic>=2.0.0` dependency for boundary validation
- `CLIContext` dataclass replacing untyped `ctx.obj` dict
- Pydantic models: `EmailSectionModel`, `LoggingConfigModel`
- `application/ports.py` with Protocol definitions; `composition/__init__.py` wiring layer

### Changed
- **BREAKING**: Full Clean Architecture refactoring into explicit layer directories (`domain/`, `application/`, `adapters/`, `composition/`)
- CLI restructured from monolithic `cli.py` into focused `cli/` package with single-responsibility modules
- Type hints modernized to Python 3.10+ style
- Removed backward compatibility re-exports; tests import from canonical module paths
- `import-linter` contracts enforce layer dependency direction
- `make test` excludes slow tests by default

## [0.2.5] - 2026-01-01

### Changed
- Bumped `lib_log_rich` to >=6.1.0 and `lib_layered_config` to >=5.2.0

## [0.2.4] - 2025-12-27

### Fixed
- Intermittent test failures on Windows when parsing JSON config output (switched to `result.stdout`)

## [0.2.3] - 2025-12-15

### Changed
- Lowered minimum Python version from 3.13 to 3.10; expanded CI matrix accordingly

## [0.2.2] - 2025-12-15

### Added
- Global `--profile` option for profile-specific configuration across all commands

### Changed
- **BREAKING**: Configuration loaded once in root CLI command and stored in Click context for subcommands
- Subcommand `--profile` options act as overrides that reload config when specified

## [0.2.0] - 2025-12-07

### Added
- `--profile` option for `config` and `config-deploy` commands
- `OutputFormat` and `DeployTarget` enums for type-safe CLI options
- LRU caching for `get_config()` (maxsize=4) and `get_default_config_path()`

### Fixed
- UTF-8 encoding issues in subprocess calls across different locales

## [0.1.0] - 2025-12-07

### Added
- Email sending via `btx-lib-mail` integration: `send-email` and `send-notification` CLI commands
- Email configuration support with `EmailConfig` dataclass and validation
- Real SMTP integration tests using `.env` configuration

## [0.0.1] - 2025-11-11
- Bootstrap
