# Configuration System

This project uses [`lib_layered_config`](https://github.com/bitranox/lib_layered_config) to manage configuration through a layered merging system. Configuration values are loaded from multiple sources and merged in a defined order, allowing flexible overrides from system-wide defaults down to individual command-line arguments.

## Key Concepts

- **Layered merging**: Configuration is assembled from multiple files and sources, with later layers overriding earlier ones
- **Cross-platform paths**: Follows XDG conventions on Linux, standard locations on macOS and Windows
- **Profile support**: Named profiles allow environment-specific configurations (e.g., `production`, `staging`, `test`)
- **TOML format**: All configuration files use TOML syntax
- **Runtime overrides**: Values can be overridden via environment variables or CLI flags without modifying files

---

## Configuration Layers

Configuration is loaded and merged in the following order (lowest to highest precedence):

| Priority | Layer        | Description                                      |
|:--------:|--------------|--------------------------------------------------|
| 1        | **defaults** | Bundled with the package (`defaultconfig.toml`)  |
| 2        | **app**      | System-wide settings for all machines            |
| 3        | **host**     | Machine-specific overrides                       |
| 4        | **user**     | User's personal settings                         |
| 5        | **.env**     | Project directory dotenv file                    |
| 6        | **env vars** | Environment variables                            |
| 7        | **CLI**      | Command-line `--set` flags (highest priority)    |

**Merge behavior**: Each layer only needs to specify values it wants to override. Unspecified values inherit from lower layers.

---

## File Locations

### Platform-Specific Paths

| Layer    | Linux                                   | macOS                                                              | Windows                                                      |
|----------|-----------------------------------------|--------------------------------------------------------------------|--------------------------------------------------------------|
| defaults | (bundled with package)                  | (bundled with package)                                             | (bundled with package)                                       |
| app      | `/etc/xdg/{slug}/config.toml`           | `/Library/Application Support/{vendor}/{app}/config.toml`          | `C:\ProgramData\{vendor}\{app}\config.toml`                  |
| host     | `/etc/xdg/{slug}/hosts/{hostname}.toml` | `/Library/Application Support/{vendor}/{app}/hosts/{hostname}.toml`| `C:\ProgramData\{vendor}\{app}\hosts\{hostname}.toml`        |
| user     | `~/.config/{slug}/config.toml`          | `~/Library/Application Support/{vendor}/{app}/config.toml`         | `%APPDATA%\{vendor}\{app}\config.toml`                       |

### Path Placeholders

| Placeholder  | Linux                        | macOS / Windows              |
|--------------|------------------------------|------------------------------|
| `{slug}`     | `fake-winreg`   | —                            |
| `{vendor}`   | —                            | `bitranox`                   |
| `{app}`      | —                            | `fake_winreg`   |
| `{hostname}` | System hostname              | System hostname              |

### Concrete Examples

**Linux:**
- User config: `~/.config/fake-winreg/config.toml`
- App config: `/etc/xdg/fake-winreg/config.toml`
- Host config: `/etc/xdg/fake-winreg/hosts/myserver.toml`

**macOS:**
- User config: `~/Library/Application Support/bitranox/fake_winreg/config.toml`

**Windows:**
- User config: `%APPDATA%\bitranox\fake_winreg\config.toml`

---

## CLI Commands

### Global Options

These options apply to all commands and must be specified **before** the command name:

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit. |
| `--profile NAME` | Load configuration from a named profile (e.g., `production`, `test`). |
| `--set SECTION.KEY=VALUE` | Override a configuration setting. Can be repeated for multiple overrides. |
| `--env-file PATH` | Explicit `.env` file path. Skips the default upward directory search. |
| `--traceback` | Show full Python traceback on errors (useful for debugging). |
| `--no-traceback` | Hide traceback, show only error message (default). |

**Example usage:**

```bash
# Use a specific profile
fake-winreg --profile production config

# Override settings at runtime (repeatable)
fake-winreg --set lib_log_rich.console_level=DEBUG config
# Load configuration from an explicit .env file
fake-winreg --env-file /etc/myapp/.env config

# Show full traceback for debugging
fake-winreg --traceback config-deploy --target user
```

---

### View Configuration

Display the merged configuration from all sources (defaults → app → host → user → .env → env vars).

#### Options Reference

| Option | Required | Description |
|--------|:--------:|-------------|
| `--format` | No | Output format: `human` (default) or `json`. |
| `--section NAME` | No | Show only a specific section (e.g., `lib_log_rich`). |
| `--profile NAME` | No | Load configuration for a specific profile. |

#### Examples

```bash
# Show merged configuration from all sources
fake-winreg config

# Output as JSON (useful for scripting)
fake-winreg config --format json

# Show specific section only
fake-winreg config --section lib_log_rich

# Load configuration for a specific profile
fake-winreg config --profile production

# Combine options
fake-winreg config --profile staging --format json --section lib_log_rich
```

### Deploy Configuration Files

Deploy bundled default configuration to platform-specific directories.

#### Options Reference

| Option | Required | Description |
|--------|:--------:|-------------|
| `--target` | Yes | Target layer: `app`, `host`, or `user`. Can be specified multiple times. |
| `--force` | No | Overwrite existing configuration files. Without this, existing files are skipped. |
| `--profile NAME` | No | Deploy to a profile-specific subdirectory (e.g., `profile/production/`). |
| `--permissions` | No | Enable Unix permission setting (default). |
| `--no-permissions` | No | Disable permission setting; use system umask instead. |
| `--dir-mode MODE` | No | Override directory permissions (octal: `750` or `0o750`). |
| `--file-mode MODE` | No | Override file permissions (octal: `640` or `0o640`). |

#### Basic Examples

```bash
# Create user configuration file
fake-winreg config-deploy --target user

# Deploy to system-wide location (requires privileges)
sudo fake-winreg config-deploy --target app

# Deploy host-specific configuration
sudo fake-winreg config-deploy --target host

# Deploy to multiple locations at once
fake-winreg config-deploy --target user --target host

# Overwrite existing configuration
fake-winreg config-deploy --target user --force

# Deploy to a specific profile directory
fake-winreg config-deploy --target user --profile production

# Deploy production profile and overwrite if exists
fake-winreg config-deploy --target user --profile production --force
```

#### Deploying for Other Users

To deploy user-level configuration for a different user account, use `sudo -u`:

```bash
# Deploy user config for 'serviceaccount' user
sudo -u serviceaccount fake-winreg config-deploy --target user

# Deploy with a specific profile
sudo -u serviceaccount fake-winreg config-deploy --target user --profile production

# The config will be created at that user's home directory:
# /home/serviceaccount/.config/fake-winreg/config.toml
```

**Important notes:**

- Using `sudo` alone (without `-u`) deploys to root's home directory, not the target user's
- Always use `sudo -u <username>` when deploying for service accounts or other users
- Files are created with ownership of the target user (correct behavior)
- File permissions are set according to the `user` layer defaults (`0o700`/`0o600` = private)

**Common deployment scenarios:**

```bash
# System admin deploying app-wide config (all users)
sudo fake-winreg config-deploy --target app

# System admin deploying for a service account
sudo -u myservice fake-winreg config-deploy --target user

# System admin deploying host-specific config
sudo fake-winreg config-deploy --target host

# Regular user deploying their own config (no sudo needed)
fake-winreg config-deploy --target user
```

#### File Permissions (POSIX Only)

On Linux and macOS, `config-deploy` sets Unix file permissions based on the target layer. Windows uses ACLs and ignores these settings.

| Target | Directory Mode | File Mode | Description |
|--------|:--------------:|:---------:|-------------|
| `app`  | `0o755` (rwxr-xr-x) | `0o644` (rw-r--r--) | World-readable for system-wide config |
| `host` | `0o755` (rwxr-xr-x) | `0o644` (rw-r--r--) | World-readable for host-specific config |
| `user` | `0o700` (rwx------) | `0o600` (rw-------)  | Private to user only |

**Permission options:**

```bash
# Skip permission setting entirely (use system umask)
fake-winreg config-deploy --target user --no-permissions

# Override directory mode (octal)
fake-winreg config-deploy --target user --dir-mode 750

# Override file mode (octal)
fake-winreg config-deploy --target user --file-mode 640

# Both overrides together
fake-winreg config-deploy --target user --dir-mode 750 --file-mode 640

# Octal formats: both "750" and "0o750" are accepted
fake-winreg config-deploy --target user --dir-mode 0o750
```

**Configurable defaults:**

Permission defaults can be customized in `[lib_layered_config.default_permissions]`:

```toml
[lib_layered_config.default_permissions]
# Values: octal strings ("0o755", "755") or decimal integers (493)
app_directory = "0o755"
app_file = "0o644"
host_directory = "0o755"
host_file = "0o644"
user_directory = "0o700"
user_file = "0o600"

# Set to false to disable permission setting by default
enabled = true
```

### Generate Example Configuration Files

Create example TOML files showing all available options with default values and documentation comments. Useful for learning the configuration structure or creating initial configuration files.

#### Options Reference

| Option | Required | Description |
|--------|:--------:|-------------|
| `--destination DIR` | Yes | Directory to write example files. |
| `--force` | No | Overwrite existing files. Without this, existing files are skipped. |

#### Examples

```bash
# Generate examples in a specific directory
fake-winreg config-generate-examples --destination ./examples

# Overwrite existing example files
fake-winreg config-generate-examples --destination ./examples --force

# Generate examples in current directory
fake-winreg config-generate-examples --destination .
```

#### Generated Files

| File | Description |
|------|-------------|
| `config.toml` | Main configuration file with all sections |
| `config.d/*.toml` | Modular configuration files (logging, etc.) |

Each file contains commented documentation explaining available options and their default values.

### Runtime Overrides

Use `--set` to override configuration values without modifying files. This option:
- Has the **highest precedence** (overrides all other sources including environment variables)
- Can be **repeated** to set multiple values
- Must appear **before** the command name

#### Syntax

```
--set SECTION.KEY=VALUE
--set SECTION.SUBSECTION.KEY=VALUE
```

#### Examples

```bash
# Override a single value
fake-winreg --set lib_log_rich.console_level=DEBUG config

# Override multiple values
fake-winreg --set lib_log_rich.console_level=DEBUG --set lib_log_rich.console_format_preset=short config

# Override with JSON arrays/objects (use single quotes around the value)
fake-winreg --set section.hosts='["a.com", "b.com"]' config

# Combine with profile
fake-winreg --profile production --set lib_log_rich.console_level=DEBUG config
```

#### Supported Value Types

| Type | Example |
|------|---------|
| String | `--set section.key=value` |
| Integer | `--set section.timeout=30` |
| Float | `--set section.ratio=0.5` |
| Boolean | `--set section.enabled=true` or `--set section.enabled=false` |
| JSON Array | `--set section.hosts='["a.com", "b.com"]'` |
| JSON Object | `--set section.metadata='{"key": "value"}'` |

---

## Profiles

Profiles provide isolated configuration namespaces for different environments (e.g., `production`, `staging`, `test`).

### Profile Name Requirements

Profile names are validated for security and cross-platform compatibility:

| Rule | Description |
|------|-------------|
| **Maximum length** | 64 characters |
| **Allowed characters** | ASCII letters (`a-z`, `A-Z`), digits (`0-9`), hyphens (`-`), underscores (`_`) |
| **Start character** | Must start with a letter or digit (not `-` or `_`) |
| **Reserved names** | Windows reserved names rejected: `CON`, `PRN`, `AUX`, `NUL`, `COM1`-`COM9`, `LPT1`-`LPT9` |
| **Path safety** | No path separators (`/`, `\`) or traversal sequences (`..`) |

**Valid examples:** `production`, `staging-v2`, `test_env`, `dev01`

**Invalid examples:** `../etc` (path traversal), `-invalid` (starts with hyphen), `CON` (Windows reserved)

### Which Layers Are Affected?

| Layer    | Affected by Profile? | Notes                               |
|----------|:--------------------:|-------------------------------------|
| defaults | No                   | Always loaded from package          |
| app      | Yes                  | Uses `profile/<name>/` subdirectory |
| host     | Yes                  | Uses `profile/<name>/` subdirectory |
| user     | Yes                  | Uses `profile/<name>/` subdirectory |
| .env     | No                   | Project directory                   |
| env vars | No                   | Environment                         |
| CLI      | No                   | Command line                        |

### Profile Path Examples

**Without profile:**
- `~/.config/fake-winreg/config.toml`

**With profile `production`:**
- `~/.config/fake-winreg/profile/production/config.toml`

### Reading Behavior

Profile directories are **separate namespaces**. Configuration deployed with a profile is only visible when reading with that same profile.

| Command                         | Sees `app` layer?                  | Sees `user` layer?                 |
|---------------------------------|------------------------------------|------------------------------------|
| `config` (no profile)           | Only if deployed without profile   | Only if deployed without profile   |
| `config --profile production`   | Only if deployed with `production` | Only if deployed with `production` |

**Example**: If you deploy `app` with `--profile production` but `user` without a profile:

| Command                       | app layer | user layer |
|-------------------------------|:---------:|:----------:|
| `config`                      | No        | Yes        |
| `config --profile production` | Yes       | No         |

---

## Environment Variables

Configuration can be overridden via environment variables using two methods:

### Method 1: Native lib_log_rich Variables

For logging configuration, use the native `LOG_*` variables (highest precedence):

```bash
LOG_CONSOLE_LEVEL=DEBUG fake-winreg hello
LOG_ENABLE_GRAYLOG=true LOG_GRAYLOG_ENDPOINT="logs.example.com:12201" fake-winreg hello
```

### Method 2: Application-Prefixed Variables

For any configuration section, use the format: `<PREFIX>___<SECTION>__<KEY>=value`

```bash
FAKE_WINREG___LIB_LOG_RICH__CONSOLE_LEVEL=DEBUG fake-winreg hello
FAKE_WINREG___LIB_LOG_RICH__CONSOLE_FORMAT_PRESET=short fake-winreg hello
```

**Separator reference:**
- `___` (triple underscore) — separates prefix from section
- `__` (double underscore) — separates section from key

---

## .env File Support

Create a `.env` file in your project directory for local development overrides:

```bash
# .env
LOG_CONSOLE_LEVEL=DEBUG
LOG_CONSOLE_FORMAT_PRESET=short
LOG_ENABLE_GRAYLOG=false
```

By default, the application searches upward from the current directory to discover `.env` files.

To load a specific `.env` file instead, use `--env-file`:

```bash
# Load from an explicit path (skips upward directory search)
fake-winreg --env-file /opt/myapp/config/.env config
fake-winreg --env-file ./environments/staging.env config
```

The file must exist and be readable; Click validates this before the command runs.

---

## Default Configuration

The `defaultconfig.toml` and files in `defaultconfig.d/` (bundled with the package) provide baseline values. These serve as the fallback when no external configuration files are deployed.

---

## Customization Best Practices

**Do NOT modify deployed configuration files directly.** These files may be overwritten during package updates.

Instead, create your own override files in the appropriate layer directory using a high-numbered prefix:

```bash
# User-level customization (Linux)
~/.config/fake-winreg/999-myconfig.toml

# User-level customization (macOS)
~/Library/Application Support/bitranox/fake_winreg/999-myconfig.toml

# User-level customization (Windows)
%APPDATA%\bitranox\fake_winreg\999-myconfig.toml

# System-wide customization (Linux)
/etc/xdg/fake-winreg/999-myconfig.toml
```

**Why this works:**
- Files in each layer directory are loaded in alphabetical order
- Higher-numbered files (e.g., `999-`) load last and override earlier values
- Your custom file won't be touched by updates that regenerate `config.toml`

**Example `999-myconfig.toml`:**

```toml
# My custom overrides - survives package updates

[lib_log_rich]
console_level = "DEBUG"
```

This approach keeps your customizations separate and safe from updates while still benefiting from new default values added in future versions.

---

## Library Use

You can import the configuration system directly in Python:

```python
import fake_winreg as btcli

# Get the merged configuration object
config = btcli.get_config()
print(config.as_dict())

# Access specific sections
log_config = config.get("lib_log_rich", default={})
```
