# Module Reference: Architecture & File Index

## Status

Complete (v1.1.2+)

---

## Related Files

### Domain Layer
- `src/fake_winreg/domain/api.py` — Public winreg-compatible API functions (CreateKey, OpenKey, QueryValueEx, etc.)
- `src/fake_winreg/domain/registry.py` — Registry tree and key management
- `src/fake_winreg/domain/memory_backend.py` — In-memory registry backend
- `src/fake_winreg/domain/handles.py` — Registry handle management
- `src/fake_winreg/domain/types.py` — Registry type definitions
- `src/fake_winreg/domain/constants.py` — Registry constants (HKEY values, access flags, value types)
- `src/fake_winreg/domain/validation.py` — Registry input validation
- `src/fake_winreg/domain/helpers.py` — Domain helper utilities
- `src/fake_winreg/domain/serialization.py` — Registry data serialization
- `src/fake_winreg/domain/test_registries.py` — Pre-built test registry fixtures
- `src/fake_winreg/domain/errors.py` — Domain exception types
- `src/fake_winreg/domain/enums.py` — Type-safe enums (OutputFormat, DeployTarget)

### Application Layer
- `src/fake_winreg/application/ports.py` — Callable Protocol definitions for adapter functions

### Adapters Layer
- `src/fake_winreg/adapters/config/loader.py` — Configuration loading with LRU caching
- `src/fake_winreg/adapters/config/deploy.py` — Configuration deployment
- `src/fake_winreg/adapters/config/display.py` — Configuration display (TOML/JSON output, redaction)
- `src/fake_winreg/adapters/config/overrides.py` — CLI `--set` override parsing and deep-merge
- `src/fake_winreg/adapters/email/sender.py` — SMTP email with EmailConfig (Pydantic)
- `src/fake_winreg/adapters/email/validation.py` — Email recipient validation
- `src/fake_winreg/adapters/logging/setup.py` — lib_log_rich initialization
- `src/fake_winreg/adapters/cli/` — CLI adapter package:
  - `__init__.py` — Public facade
  - `constants.py` — Shared constants
  - `exit_codes.py` — POSIX exit codes (ExitCode IntEnum)
  - `traceback.py` — Traceback state management
  - `context.py` — Click context helpers
  - `root.py` — Root command group
  - `main.py` — Entry point
  - `commands/info.py` — info command
  - `commands/config.py` — config, config-deploy, config-generate-examples commands
  - `commands/email.py` — send-email, send-notification commands
  - `commands/logging.py` — logdemo command

### Adapters Layer (In-Memory / Testing)
- `src/fake_winreg/adapters/memory/__init__.py` — Public facade + Protocol conformance assertions
- `src/fake_winreg/adapters/memory/config.py` — In-memory config adapters
- `src/fake_winreg/adapters/memory/email.py` — In-memory email adapters
- `src/fake_winreg/adapters/memory/logging.py` — In-memory logging (no-op)

### Composition Layer
- `src/fake_winreg/composition/__init__.py` — Wires adapters to ports

### Entry Points
- `src/fake_winreg/__main__.py` — Thin shim for `python -m`
- `src/fake_winreg/__init__.py` — Public API exports
- `src/fake_winreg/__init__conf__.py` — Package metadata constants

### Configuration Defaults
- `src/fake_winreg/adapters/config/defaultconfig.toml` — Base defaults
- `src/fake_winreg/adapters/config/defaultconfig.d/40-layered-config.toml` — lib_layered_config integration docs
- `src/fake_winreg/adapters/config/defaultconfig.d/50-mail.toml` — Email defaults
- `src/fake_winreg/adapters/config/defaultconfig.d/90-logging.toml` — Logging defaults

### Tests
- `tests/test_registry.py` — Registry tree and key management tests
- `tests/test_registry_api.py` — winreg-compatible API function tests
- `tests/test_reg_io.py` — Registry I/O tests
- `tests/test_backend_json.py` — JSON backend tests
- `tests/test_backend_sqlite.py` — SQLite backend tests
- `tests/test_convert.py` — Registry data conversion tests
- `tests/test_cache_effectiveness.py` — LRU cache behavior tests
- `tests/test_cli_core.py` — Core CLI command tests
- `tests/test_cli_config.py` — Config CLI command tests
- `tests/test_cli_email.py` — Email CLI command tests
- `tests/test_cli_env_file.py` — Env file CLI option tests
- `tests/test_cli_exit_codes.py` — Exit code tests
- `tests/test_cli_overrides.py` — CLI override tests
- `tests/test_cli_validation.py` — CLI validation tests
- `tests/test_config_overrides.py` — `--set` parsing tests
- `tests/test_display.py` — Config display formatting tests
- `tests/test_deploy_permissions.py` — Deploy permission tests
- `tests/test_enums.py` — Enum tests
- `tests/test_errors.py` — Error type tests
- `tests/test_logging.py` — Logging tests
- `tests/test_mail.py` — Email configuration and sending tests
- `tests/test_metadata.py` — Package metadata tests
- `tests/test_metadata_sync.py` — Metadata sync tests
- `tests/test_module_entry.py` — `python -m` entry tests
- `tests/test_ports.py` — Protocol conformance tests
- `tests/test_property_email.py` — Email property tests
- `tests/test_property_overrides.py` — Override property tests

---

## Architecture

### Layer Assignments

| Directory/Module | Layer | Responsibility |
|------------------|-------|----------------|
| `domain/` | Domain | Pure logic — no I/O, logging, or frameworks |
| `application/ports.py` | Application | Protocol definitions for adapters |
| `adapters/config/` | Adapters | Configuration loading, deployment, display |
| `adapters/email/` | Adapters | SMTP email sending |
| `adapters/logging/` | Adapters | lib_log_rich initialization |
| `adapters/cli/` | Adapters | Click CLI framework integration |
| `adapters/memory/` | Adapters | In-memory implementations for testing |
| `composition/` | Composition | Wires adapters to ports |

### Import Enforcement

Layer boundaries enforced via `import-linter` contracts in `pyproject.toml`:
- **Domain is pure**: Cannot import from adapters or composition
- **Clean Architecture layers**: Validates dependency direction (composition → adapters → application → domain)

Run `lint-imports` to verify compliance.

---

## Exit Codes

POSIX-conventional exit codes defined in `adapters/cli/exit_codes.py`:

| Code | Name | Usage |
|------|------|-------|
| 0 | `SUCCESS` | Command completed successfully |
| 1 | `GENERAL_ERROR` | Unhandled exception, general failure |
| 2 | `FILE_NOT_FOUND` | Attachment or file not found |
| 13 | `PERMISSION_DENIED` | Cannot write to target directory |
| 22 | `INVALID_ARGUMENT` | Invalid CLI argument or section not found |
| 69 | `SMTP_FAILURE` | SMTP delivery failed |
| 78 | `CONFIG_ERROR` | Missing required configuration |
| 110 | `TIMEOUT` | Operation timed out |
| 130 | `SIGNAL_INT` | Interrupted (SIGINT/Ctrl+C) |
| 141 | `BROKEN_PIPE` | Output pipe closed |
| 143 | `SIGNAL_TERM` | Terminated (SIGTERM) |

---

## CLI Commands

### Root Command

**Command:** `fake-winreg`

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit |
| `--traceback / --no-traceback` | Show full Python traceback on errors |
| `--profile NAME` | Load configuration from a named profile |
| `--set SECTION.KEY=VALUE` | Override configuration setting (repeatable) |
| `-h, --help` | Show help and exit |

### info

Print resolved package metadata.

**Exit codes:** 0

### config

Display merged configuration from all sources.

| Option | Description |
|--------|-------------|
| `--format [human\|json]` | Output format (default: human) |
| `--section NAME` | Show only specific section |

**Exit codes:** 0, 22 (section not found)

### config-deploy

Deploy default configuration to system or user directories.

| Option | Description |
|--------|-------------|
| `--target [app\|host\|user]` | Target layer(s) — required, repeatable |
| `--force` | Overwrite existing files |
| `--profile NAME` | Deploy to profile subdirectory |

**Exit codes:** 0, 1, 13 (permission denied)

### config-generate-examples

Generate example configuration files.

| Option | Description |
|--------|-------------|
| `--destination DIR` | Target directory — required |
| `--force` | Overwrite existing files |

**Exit codes:** 0, 1

### send-email

Send email using configured SMTP settings.

| Option | Description |
|--------|-------------|
| `--to ADDRESS` | Recipient (repeatable) |
| `--subject TEXT` | Subject line — required |
| `--body TEXT` | Plain-text body |
| `--body-html TEXT` | HTML body |
| `--from ADDRESS` | Override sender |
| `--attachment PATH` | File to attach (repeatable) |
| `--smtp-host HOST:PORT` | Override SMTP host (repeatable) |
| `--smtp-username USER` | Override username |
| `--smtp-password PASS` | Override password |
| `--use-starttls / --no-use-starttls` | Override STARTTLS |
| `--timeout SECONDS` | Override timeout |

**Exit codes:** 0, 2 (file not found), 22, 69 (SMTP failure), 78 (no SMTP hosts)

### send-notification

Send simple plain-text notification email.

| Option | Description |
|--------|-------------|
| `--to ADDRESS` | Recipient (repeatable) |
| `--subject TEXT` | Subject — required |
| `--message TEXT` | Message — required |
| `--from ADDRESS` | Override sender |
| `--smtp-host HOST:PORT` | Override SMTP host (repeatable) |
| `--smtp-username USER` | Override username |
| `--smtp-password PASS` | Override password |
| `--use-starttls / --no-use-starttls` | Override STARTTLS |
| `--timeout SECONDS` | Override timeout |

**Exit codes:** 0, 22, 69 (SMTP failure), 78 (no SMTP hosts)

### logdemo

Run logging demonstration.

| Option | Description |
|--------|-------------|
| `--theme NAME` | Logging theme (default: classic) |

**Exit codes:** 0

---

## Profile Validation

Profile names (`--profile` option) are validated using `lib_layered_config.validate_profile_name()`.

### validate_profile()

**Location:** `adapters/config/loader.py`

```python
def validate_profile(profile: str, max_length: int | None = None) -> None:
    """Validate profile name using lib_layered_config."""
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `profile` | `str` | required | Profile name to validate |
| `max_length` | `int \| None` | 64 | Maximum length (DEFAULT_MAX_PROFILE_LENGTH) |

### Validation Rules

| Rule | Description |
|------|-------------|
| Maximum length | 64 characters (configurable via `max_length`) |
| Character set | ASCII alphanumeric, hyphens (`-`), underscores (`_`) |
| Start character | Must start with alphanumeric character |
| Empty string | Rejected |
| Windows reserved | CON, PRN, AUX, NUL, COM1-9, LPT1-9 rejected |
| Path traversal | `/`, `\`, `..` rejected |
| Control chars | Rejected |

### Error Handling

Raises `ValueError` with descriptive message on invalid input.

---

## Email Configuration

### EmailConfig Fields

The `EmailConfig` Pydantic model (`adapters/email/sender.py`) provides validated, immutable email configuration:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `smtp_hosts` | `list[str]` | `[]` | SMTP servers in `host[:port]` format |
| `from_address` | `str \| None` | `None` | Default sender address |
| `recipients` | `list[str]` | `[]` | Default recipient addresses |
| `smtp_username` | `str \| None` | `None` | SMTP authentication username |
| `smtp_password` | `str \| None` | `None` | SMTP authentication password |
| `use_starttls` | `bool` | `True` | Enable STARTTLS negotiation |
| `timeout` | `float` | `30.0` | Socket timeout in seconds |
| `raise_on_missing_attachments` | `bool` | `True` | Raise on missing attachment files |
| `raise_on_invalid_recipient` | `bool` | `True` | Raise on invalid recipient addresses |

### Attachment Security Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `attachment_allowed_extensions` | `frozenset[str] \| None` | `None` | Whitelist of allowed extensions |
| `attachment_blocked_extensions` | `frozenset[str] \| None` | `None` | Blacklist of blocked extensions |
| `attachment_allowed_directories` | `frozenset[Path] \| None` | `None` | Whitelist of allowed source directories |
| `attachment_blocked_directories` | `frozenset[Path] \| None` | `None` | Blacklist of blocked directories |
| `attachment_max_size_bytes` | `int \| None` | `26_214_400` | Maximum file size (25 MiB), `None` to disable |
| `attachment_allow_symlinks` | `bool` | `False` | Whether symlinks are permitted |
| `attachment_raise_on_security_violation` | `bool` | `True` | Raise or skip on security violation |

**Notes:**
- `None` values use `btx_lib_mail`'s OS-specific defaults (blocked extensions/directories)
- Empty arrays `[]` in TOML configuration are coerced to `None`
- `max_size_bytes = 0` is coerced to `None` (disable size checking)
- String paths are converted to `Path` objects during validation

### Configuration Loading

`load_email_config_from_dict()` handles the nested `[email.attachments]` TOML section:

```python
# TOML structure:
# [email]
# smtp_hosts = ["smtp.example.com:587"]
# [email.attachments]
# max_size_bytes = 10485760

config = load_email_config_from_dict(config_dict)
# Flattens to: attachment_max_size_bytes = 10485760
```

---

## Testing Infrastructure

### In-Memory Adapters

The `adapters/memory/` package provides lightweight implementations for testing:

| Module | Protocols Satisfied |
|--------|---------------------|
| `memory/config.py` | `GetConfig`, `GetDefaultConfigPath`, `DeployConfiguration`, `DisplayConfig` |
| `memory/email.py` | `SendEmail`, `SendNotification`, `LoadEmailConfigFromDict` |
| `memory/logging.py` | `InitLogging` |

Use `composition.build_testing()` to wire all in-memory adapters.

### Test Fixtures (conftest.py)

| Fixture | Purpose |
|---------|---------|
| `config_factory` | Creates real `Config` instances from test data |
| `inject_config` | Injects config into CLI path |
| `cli_runner` | Fresh `CliRunner` per test |
| `strip_ansi` | Strips ANSI escape codes from output |
| `clear_config_cache` | Clears LRU cache before tests |
| `managed_traceback_state` | Resets/restores traceback configuration |

---

**Last Updated:** 2026-01-30 (attachment security)
