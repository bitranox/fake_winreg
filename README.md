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


`fake_winreg` is a template CLI application demonstrating configuration management and structured logging. It showcases rich-click for ergonomics and lib_cli_exit_tools for exits, providing a solid foundation for building CLI applications.
- CLI entry point styled with rich-click (rich output + click ergonomics).
- Layered configuration system with lib_layered_config (defaults → app → host → user → .env → env).
- Rich structured logging with lib_log_rich (console, journald, eventlog, Graylog/GELF).
- Exit-code and messaging helpers powered by lib_cli_exit_tools.
- Metadata helpers ready for packaging, testing, and release automation.


### Python 3.10+ Baseline

- The project targets **Python 3.10 and newer**.
- Runtime dependencies require current stable releases (`rich-click>=1.9.6`
  and `lib_cli_exit_tools>=2.2.4`). Dev dependencies (pytest, ruff, pyright,
  bandit, etc.) specify minimum version constraints to ensure compatibility.
- CI workflows exercise GitHub's rolling runner images (`ubuntu-latest`,
  `macos-latest`, `windows-latest`) and cover CPython 3.10 through 3.14
  alongside the latest available 3.x release provided by Actions.

---

## Install - recommended via uv

[uv](https://docs.astral.sh/uv/) is an ultrafast Python package manager written in Rust (10-20x faster than pip/poetry).

### Install uv (if not already installed) 
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy the actual binaries
cp /root/.local/bin/uv /usr/local/bin/uv
cp /root/.local/bin/uvx /usr/local/bin/uvx

# Ensure world-executable
chmod 755 /usr/local/bin/uv /usr/local/bin/uvx

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### One-shot run (no install needed)

```bash
uvx fake_winreg@latest --help
```

### Persistent install as CLI tool

```bash
# Install latest python
install_latest_python_gcc.sh
# pin uv to the latest python
uv python pin /opt/python-latest/bin/python3
# One-time install, persists from the git repo
uv tool install --python /opt/python-latest/bin/python3 --from "git+https://github.com/bitranox/fake_winreg.git" fake-winreg
# or One-time install, persists from PyPi
uv tool install --python /opt/python-latest/bin/python3 fake-winreg
# Update (requires network)
uv tool upgrade fake-winreg
# Run
fake-winreg --help
```

### Persistent install as CLI tool
```bash
# install the CLI tool (isolated environment, added to PATH)
uv tool install fake_winreg

# upgrade to latest
uv tool upgrade fake_winreg
```

### Install as project dependency

```bash
uv venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
uv pip install fake_winreg
```

For alternative install paths (pip, pipx, source builds, etc.), see
[INSTALL.md](INSTALL.md). All supported methods register both the
`fake_winreg` and `fake-winreg` commands on your PATH.

---

## Configuration

See [CONFIG.md](CONFIG.md) for detailed documentation on the layered configuration system, including precedence rules, profile support, and customization best practices.

---

## Quick Start

```bash
# Install
uv tool install fake_winreg

# Verify
fake-winreg --version

# Try it out
fake-winreg hello
fake-winreg info
fake-winreg config
```

---

## Usage

The CLI leverages [rich-click](https://github.com/ewels/rich-click) so help output, validation errors, and prompts render with Rich styling while keeping the familiar click ergonomics.

### Available Commands

```bash
# Display package information
fake-winreg info

# Greeting and error-handling demos
fake-winreg hello
fake-winreg fail
fake-winreg --traceback fail

# Configuration management
fake-winreg config                         # Show current configuration
fake-winreg config --format json           # Show as JSON
fake-winreg config --section lib_log_rich  # Show specific section
fake-winreg config --profile production    # Use a named profile

# Deploy configuration templates to target directories
# Without profile:
fake-winreg config-deploy --target app    # → /etc/xdg/{slug}/config.toml
fake-winreg config-deploy --target host   # → /etc/xdg/{slug}/hosts/{hostname}.toml
fake-winreg config-deploy --target user   # → ~/.config/{slug}/config.toml

# With profile:
fake-winreg config-deploy --target app --profile production   # → /etc/xdg/{slug}/profile/production/config.toml
fake-winreg config-deploy --target host --profile production  # → /etc/xdg/{slug}/profile/production/hosts/{hostname}.toml
fake-winreg config-deploy --target user --profile production  # → ~/.config/{slug}/profile/production/config.toml

# With custom permissions (POSIX only):
fake-winreg config-deploy --target user --file-mode 640       # Files with rw-r----- (640)
fake-winreg config-deploy --target user --dir-mode 750        # Directories with rwxr-x--- (750)
fake-winreg config-deploy --target app --no-permissions       # Skip permission setting (use umask)

# Profile names: alphanumeric, hyphens, underscores; max 64 chars; must start with letter/digit
# See CONFIG.md for full validation rules

# Deploy configuration examples
fake-winreg config-generate-examples --destination ./examples

# Load configuration from an explicit .env file (skips upward directory search)
fake-winreg --env-file /path/to/.env config
fake-winreg --env-file ./environments/production.env send-notification ...

# Override configuration at runtime (repeatable --set)
fake-winreg --set lib_log_rich.console_level=DEBUG config
fake-winreg --set email.smtp_hosts='["smtp.example.com:587"]' config --format json

# Logging demo
fake-winreg logdemo
fake-winreg --set lib_log_rich.console_level=DEBUG logdemo

# Send email
fake-winreg send-email \
    --to recipient@example.com \
    --subject "Test Email" \
    --body "Hello from bitranox!"

# Send email with HTML body and attachments
fake-winreg send-email \
    --to recipient@example.com \
    --subject "Monthly Report" \
    --body "See attached." \
    --body-html "<h1>Report</h1><p>Details in the PDF.</p>" \
    --attachment report.pdf

# Send plain-text notification
fake-winreg send-notification \
    --to ops@example.com \
    --subject "Deploy OK" \
    --message "Application deployed successfully"

# All commands work with any entry point
python -m fake_winreg info
uvx fake_winreg info
```

---

### Email Sending

The application includes email sending capabilities via [btx-lib-mail](https://pypi.org/project/btx-lib-mail/), supporting both simple notifications and rich HTML emails with attachments.

#### Email Configuration

Configure email settings via environment variables, `.env` file, or configuration files:

**Environment Variables:**

Environment variables use the format: `<PREFIX>___<SECTION>__<KEY>=value`
- Triple underscore (`___`) separates PREFIX from SECTION
- Double underscore (`__`) separates SECTION from KEY

```bash
export FAKE_WINREG___EMAIL__SMTP_HOSTS="smtp.gmail.com:587,smtp.backup.com:587"
export FAKE_WINREG___EMAIL__FROM_ADDRESS="alerts@myapp.com"
export FAKE_WINREG___EMAIL__SMTP_USERNAME="your-email@gmail.com"
export FAKE_WINREG___EMAIL__SMTP_PASSWORD="your-app-password"
export FAKE_WINREG___EMAIL__USE_STARTTLS="true"
export FAKE_WINREG___EMAIL__TIMEOUT="60.0"
```

**Configuration File**:
```toml
[email]
smtp_hosts = ["smtp.gmail.com:587", "smtp.backup.com:587"]  # Fallback to backup if primary fails
from_address = "alerts@myapp.com"
smtp_username = "myuser@gmail.com"
smtp_password = "secret_password"  # Consider using environment variables for sensitive data
use_starttls = true
timeout = 60.0
```

**`.env` File:**
```bash
# Email configuration for local testing
FAKE_WINREG___EMAIL__SMTP_HOSTS=smtp.gmail.com:587
FAKE_WINREG___EMAIL__FROM_ADDRESS=noreply@example.com
```

#### Gmail Configuration Example

For Gmail, create an [App Password](https://support.google.com/accounts/answer/185833) instead of using your account password:

```bash
FAKE_WINREG___EMAIL__SMTP_HOSTS=smtp.gmail.com:587
FAKE_WINREG___EMAIL__FROM_ADDRESS=your-email@gmail.com
FAKE_WINREG___EMAIL__SMTP_USERNAME=your-email@gmail.com
FAKE_WINREG___EMAIL__SMTP_PASSWORD=your-16-char-app-password
```

#### Send Simple Email

```bash
# Send basic email to one recipient
fake-winreg send-email \
    --to recipient@example.com \
    --subject "Test Email" \
    --body "Hello from bitranox!"

# Send to multiple recipients
fake-winreg send-email \
    --to user1@example.com \
    --to user2@example.com \
    --subject "Team Update" \
    --body "Please review the latest changes"
```

#### Send HTML Email with Attachments

```bash
fake-winreg send-email \
    --to recipient@example.com \
    --subject "Monthly Report" \
    --body "Please find the monthly report attached." \
    --body-html "<h1>Monthly Report</h1><p>See attached PDF for details.</p>" \
    --attachment report.pdf \
    --attachment data.csv
```

#### Send Notifications

For simple plain-text notifications, use the convenience command:

```bash
# Single recipient
fake-winreg send-notification \
    --to ops@example.com \
    --subject "Deployment Success" \
    --message "Application deployed successfully to production at $(date)"

# Multiple recipients
fake-winreg send-notification \
    --to admin1@example.com \
    --to admin2@example.com \
    --subject "System Alert" \
    --message "Database backup completed successfully"
```

#### Programmatic Email Usage

```python
from fake_winreg.adapters.email.sender import EmailConfig
from fake_winreg.composition import send_email, send_notification

# Configure email
config = EmailConfig(
    smtp_hosts=["smtp.gmail.com:587"],
    from_address="alerts@myapp.com",
    smtp_username="myuser@gmail.com",
    smtp_password="app-password",
    timeout=60.0,
)

# Send simple email
send_email(
    config=config,
    recipients="recipient@example.com",
    subject="Test Email",
    body="Hello from Python!",
)

# Send email with HTML and attachments
from pathlib import Path
send_email(
    config=config,
    recipients=["user1@example.com", "user2@example.com"],
    subject="Report",
    body="See attached report",
    body_html="<h1>Report</h1><p>Details in attachment</p>",
    attachments=[Path("report.pdf")],
)

# Send notification
send_notification(
    config=config,
    recipients="ops@example.com",
    subject="Deployment Complete",
    message="Production deployment finished successfully",
)
```

#### Email Troubleshooting

**Connection Failures:**
- Verify SMTP hostname and port are correct
- Check firewall allows outbound connections on SMTP port
- Test connectivity: `telnet smtp.gmail.com 587`

**Authentication Errors:**
- For Gmail: Use App Password, not account password
- Ensure username/password are correct
- Check for 2FA requirements

**Emails Not Arriving:**
- Check recipient's spam folder
- Verify `from_address` is valid and not blacklisted
- Review SMTP server logs for delivery status

## Further Documentation

- [Install Guide](INSTALL.md)
- [Development Handbook](DEVELOPMENT.md)
- [Contributor Guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Module Reference](docs/systemdesign/module_reference.md)
- [License](LICENSE)
