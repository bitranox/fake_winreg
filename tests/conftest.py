"""Shared pytest fixtures for CLI and module-entry tests.

Centralizes test infrastructure following clean architecture principles:
- All shared fixtures live here
- Tests import fixtures implicitly via pytest's conftest discovery
- Fixtures use descriptive names that read as plain English
"""

from __future__ import annotations

import contextlib
import os
import re
import tempfile
from collections.abc import Callable, Iterator
from dataclasses import fields
from pathlib import Path
from typing import TYPE_CHECKING, Any

import lib_cli_exit_tools
import pytest
from click.testing import CliRunner
from lib_layered_config import Config
from lib_layered_config.domain.config import SourceInfo

if TYPE_CHECKING:
    from fake_winreg.composition import AppServices

_COVERAGE_BASENAME = ".coverage.fake_winreg"


def _purge_stale_coverage_files(cov_path: Path) -> None:
    """Delete leftover SQLite database and journal files from crashed runs.

    A prior crash can leave ``-journal``, ``-wal``, or ``-shm`` sidecar
    files next to the coverage database.  SQLite interprets those as an
    incomplete transaction and may raise ``database is locked`` on the
    next open.

    Note:
        We use an explicit suffix list rather than glob (``cov_path.parent.glob(f"{cov_path.name}*")``)
        because glob could match unrelated files sharing the same prefix. The SQLite WAL-mode
        sidecar suffixes are well-documented and stable across versions.
    """
    for suffix in ("", "-journal", "-wal", "-shm"):
        with contextlib.suppress(FileNotFoundError):
            Path(str(cov_path) + suffix).unlink()


def pytest_configure(config: pytest.Config) -> None:
    """Redirect the coverage database to a **local** temp directory.

    coverage.py stores trace data in a SQLite database.  SQLite requires
    POSIX file-locking semantics that network mounts (SMB / NFS) do not
    reliably provide, and stale journal files from a previous crash can
    trigger *"database is locked"* on Python 3.14's free-threaded build.

    This hook runs **before** ``pytest-cov``'s ``pytest_sessionstart``
    creates the ``Coverage()`` object, so the ``COVERAGE_FILE`` value is
    picked up regardless of how pytest is invoked (CI, ``make test``,
    bare ``pytest --cov``).
    """
    if "COVERAGE_FILE" not in os.environ:
        cov_path = Path(tempfile.gettempdir()) / _COVERAGE_BASENAME
        _purge_stale_coverage_files(cov_path)
        os.environ["COVERAGE_FILE"] = str(cov_path)


def _load_dotenv() -> None:
    """Load .env file when it exists for integration test configuration."""
    try:
        from dotenv import load_dotenv

        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            load_dotenv(env_file)
    except ImportError:
        pass


_load_dotenv()

ANSI_ESCAPE_PATTERN = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
CONFIG_FIELDS: tuple[str, ...] = tuple(field.name for field in fields(type(lib_cli_exit_tools.config)))


def _remove_ansi_codes(text: str) -> str:
    """Return *text* stripped of ANSI escape sequences."""
    return ANSI_ESCAPE_PATTERN.sub("", text)


def _snapshot_cli_config() -> dict[str, object]:
    """Capture every attribute from ``lib_cli_exit_tools.config``."""
    return {name: getattr(lib_cli_exit_tools.config, name) for name in CONFIG_FIELDS}


def _restore_cli_config(snapshot: dict[str, object]) -> None:
    """Reapply a configuration snapshot captured by ``_snapshot_cli_config``."""
    for name, value in snapshot.items():
        setattr(lib_cli_exit_tools.config, name, value)


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a fresh CliRunner per test.

    Click 8.x provides separate result.stdout and result.stderr attributes.
    Use result.stdout for clean output (e.g., JSON parsing) to avoid
    async log messages from stderr contaminating the output.

    Returns:
        CliRunner: A fresh Click test runner instance.

    Example:
        def test_help(cli_runner: CliRunner) -> None:
            result = cli_runner.invoke(cli, ["--help"])
            assert result.exit_code == 0
    """
    return CliRunner()


@pytest.fixture
def production_factory() -> Callable[[], AppServices]:
    """Provide the production services factory for tests.

    Use this when invoking CLI commands that don't need custom injection.
    Returns the ``build_production`` factory which wires real adapters.

    Returns:
        Callable[[], AppServices]: Factory returning production-wired AppServices.

    Example:
        def test_info(cli_runner: CliRunner, production_factory: Callable[[], AppServices]) -> None:
            result = cli_runner.invoke(cli, ["info"], obj=production_factory)
            assert result.exit_code == 0
    """
    from fake_winreg.composition import build_production

    return build_production


@pytest.fixture
def strip_ansi() -> Callable[[str], str]:
    """Return a helper that strips ANSI escape sequences from a string.

    Useful for comparing CLI output that may contain rich formatting
    (colors, bold, etc.) against expected plain text.

    Returns:
        Callable[[str], str]: Function that removes ANSI codes from input.

    Example:
        def test_output(cli_runner: CliRunner, strip_ansi: Callable[[str], str]) -> None:
            result = cli_runner.invoke(cli, ["info"])
            plain = strip_ansi(result.output)
            assert "version" in plain
    """

    def _strip(value: str) -> str:
        return _remove_ansi_codes(value)

    return _strip


@pytest.fixture
def managed_traceback_state() -> Iterator[None]:
    """Reset traceback flags to a known baseline and restore after the test.

    Combines the responsibilities of the former ``isolated_traceback_config``
    (reset to clean state) and ``preserve_traceback_state`` (snapshot/restore)
    into a single fixture.  Use this whenever a test reads or mutates the
    global ``lib_cli_exit_tools.config`` traceback flags.

    Yields:
        None: Test runs with isolated traceback state.

    Example:
        def test_traceback_flag(managed_traceback_state: None) -> None:
            lib_cli_exit_tools.config.traceback = True
            # State automatically restored after test
    """
    lib_cli_exit_tools.reset_config()
    lib_cli_exit_tools.config.traceback = False
    lib_cli_exit_tools.config.traceback_force_color = False
    snapshot = _snapshot_cli_config()
    try:
        yield
    finally:
        _restore_cli_config(snapshot)


@pytest.fixture
def clear_config_cache() -> Iterator[None]:
    """Clear the get_config lru_cache before each test.

    Note: Only clears before, not after, to avoid errors when the function
    has been monkeypatched during the test (losing cache_clear method).

    Yields:
        None: Test runs with cleared config cache.

    Example:
        def test_config_reload(clear_config_cache: None) -> None:
            config1 = get_config()
            # Cache was cleared, so this is a fresh load
    """
    from fake_winreg.adapters.config import loader as config_mod

    config_mod.get_config.cache_clear()
    yield


@pytest.fixture
def config_factory() -> Callable[[dict[str, Any]], Config]:
    """Create real Config instances from test data dicts.

    Builds actual ``lib_layered_config.Config`` objects without filesystem I/O.
    The second argument (empty dict) represents no source provenance info.

    Returns:
        Callable[[dict[str, Any]], Config]: Factory that creates Config from dict.

    Example:
        def test_email_section(config_factory: Callable[[dict[str, Any]], Config]) -> None:
            config = config_factory({"email": {"smtp_hosts": ["smtp.test.com:587"]}})
            assert config.get("email.smtp_hosts") == ["smtp.test.com:587"]
    """

    def _factory(data: dict[str, Any]) -> Config:
        return Config(data, {})

    return _factory


@pytest.fixture
def source_info_factory() -> Callable[[str, str, str | None], SourceInfo]:
    """Create SourceInfo dicts for provenance-tracking tests.

    Reduces coupling to the SourceInfo TypedDict structure.  If
    ``lib_layered_config`` adds or renames keys, only this factory
    needs updating.

    Returns:
        Callable[[str, str, str | None], SourceInfo]: Factory creating SourceInfo dicts.

    Example:
        def test_provenance(source_info_factory: Callable[..., SourceInfo]) -> None:
            info = source_info_factory("email.smtp_hosts", "user", "/home/user/.config/...")
            assert info["layer"] == "user"
    """

    def _factory(key: str, layer: str, path: str | None = None) -> SourceInfo:
        return {"layer": layer, "path": path, "key": key}

    return _factory


@pytest.fixture
def inject_config(
    clear_config_cache: None,
) -> Callable[[Config], Callable[[], AppServices]]:
    """Return a factory that provides test services with injected Config.

    Creates a services factory with the injected config loader,
    avoiding filesystem I/O while exercising the real Config API.
    Only replaces the I/O boundary (``get_config``), not the Config object itself.

    Args:
        clear_config_cache: Implicit fixture dependency ensuring cache is cleared.

    Returns:
        Callable[[Config], Callable[[], AppServices]]: Function that accepts a Config
            and returns a services factory callable suitable for ``cli_runner.invoke(obj=...)``.

    Example:
        def test_config_display(
            cli_runner: CliRunner,
            config_factory: Callable[[dict[str, Any]], Config],
            inject_config: Callable[[Config], Callable[[], AppServices]],
        ) -> None:
            config = config_factory({"section": {"key": "value"}})
            factory = inject_config(config)
            result = cli_runner.invoke(cli, ["config"], obj=factory)
            assert "key" in result.output
    """
    from fake_winreg.composition import AppServices, build_production

    def _inject(config: Config) -> Callable[[], AppServices]:
        def _fake_get_config(**_kwargs: Any) -> Config:
            return config

        prod = build_production()
        test_services = AppServices(
            get_config=_fake_get_config,
            get_default_config_path=prod.get_default_config_path,
            deploy_configuration=prod.deploy_configuration,
            display_config=prod.display_config,
            init_logging=prod.init_logging,
        )
        return lambda: test_services

    return _inject


@pytest.fixture
def inject_config_with_profile_capture(
    clear_config_cache: None,
) -> Callable[[Config, list[str | None]], Callable[[], AppServices]]:
    """Return a factory that captures profile arguments during get_config.

    Creates a services factory with a get_config that records profile
    arguments for assertion in tests verifying --profile propagation.

    Args:
        clear_config_cache: Implicit fixture dependency ensuring cache is cleared.

    Returns:
        Callable[[Config, list[str | None]], Callable[[], AppServices]]: Function
            that accepts (Config, capture_list) and returns a services factory.
            Profile values passed to get_config are appended to capture_list.

    Example:
        def test_profile_passed(
            cli_runner: CliRunner,
            config_factory: Callable[[dict[str, Any]], Config],
            inject_config_with_profile_capture: Callable[..., Callable[[], AppServices]],
        ) -> None:
            captured: list[str | None] = []
            config = config_factory({})
            factory = inject_config_with_profile_capture(config, captured)
            cli_runner.invoke(cli, ["--profile", "staging", "config"], obj=factory)
            assert captured == ["staging"]
    """
    from fake_winreg.composition import AppServices, build_production

    def _inject(config: Config, captured_profiles: list[str | None]) -> Callable[[], AppServices]:
        def _capturing_get_config(*, profile: str | None = None, **_kwargs: Any) -> Config:
            captured_profiles.append(profile)
            return config

        prod = build_production()
        test_services = AppServices(
            get_config=_capturing_get_config,
            get_default_config_path=prod.get_default_config_path,
            deploy_configuration=prod.deploy_configuration,
            display_config=prod.display_config,
            init_logging=prod.init_logging,
        )
        return lambda: test_services

    return _inject


@pytest.fixture
def inject_deploy_with_profile_capture(
    clear_config_cache: None,
) -> Callable[[Path, list[str | None]], Callable[[], AppServices]]:
    """Return a factory with deploy_configuration that captures profile arguments.

    Creates a services factory with a deploy_configuration that records
    profile arguments for assertion in tests verifying --profile propagation
    to deployment operations.

    Args:
        clear_config_cache: Implicit fixture dependency ensuring cache is cleared.

    Returns:
        Callable[[Path, list[str | None]], Callable[[], AppServices]]: Function
            that accepts (deployed_path, capture_list) and returns a services factory.
            The fake deploy always returns [deployed_path] and appends profile to capture_list.

    Example:
        def test_deploy_profile(
            cli_runner: CliRunner,
            tmp_path: Path,
            inject_deploy_with_profile_capture: Callable[..., Callable[[], AppServices]],
        ) -> None:
            captured: list[str | None] = []
            factory = inject_deploy_with_profile_capture(tmp_path / "config.toml", captured)
            cli_runner.invoke(cli, ["--profile", "prod", "config-deploy", ...], obj=factory)
            assert captured == ["prod"]
    """
    from fake_winreg.composition import AppServices, build_production

    def _inject(deployed_path: Path, captured_profiles: list[str | None]) -> Callable[[], AppServices]:
        def _capturing_deploy(
            *,
            targets: Any,
            force: bool = False,
            profile: str | None = None,
            set_permissions: bool = True,
            dir_mode: int | None = None,
            file_mode: int | None = None,
        ) -> list[Path]:
            captured_profiles.append(profile)
            return [deployed_path]

        prod = build_production()
        test_services = AppServices(
            get_config=prod.get_config,
            get_default_config_path=prod.get_default_config_path,
            deploy_configuration=_capturing_deploy,
            display_config=prod.display_config,
            init_logging=prod.init_logging,
        )
        return lambda: test_services

    return _inject


@pytest.fixture
def inject_deploy_configuration() -> Callable[[Callable[..., list[Path]]], Callable[[], AppServices]]:
    """Return a factory with a custom deploy_configuration function.

    Creates a services factory with the provided deploy_configuration
    function while keeping other services as production. Use this for
    testing deploy behavior with custom implementations (mocks, spies).

    Returns:
        Callable[[Callable[..., list[Path]]], Callable[[], AppServices]]: Function
            that accepts a deploy function and returns a services factory.

    Example:
        def test_deploy_called(
            cli_runner: CliRunner,
            inject_deploy_configuration: Callable[..., Callable[[], AppServices]],
        ) -> None:
            calls = []
            def spy_deploy(**kwargs) -> list[Path]:
                calls.append(kwargs)
                return [Path("/fake/path")]
            factory = inject_deploy_configuration(spy_deploy)
            cli_runner.invoke(cli, ["config-deploy", "--target", "user"], obj=factory)
            assert len(calls) == 1
    """
    from fake_winreg.composition import AppServices, build_production

    def _inject(deploy_fn: Callable[..., list[Path]]) -> Callable[[], AppServices]:
        prod = build_production()
        test_services = AppServices(
            get_config=prod.get_config,
            get_default_config_path=prod.get_default_config_path,
            deploy_configuration=deploy_fn,
            display_config=prod.display_config,
            init_logging=prod.init_logging,
        )
        return lambda: test_services

    return _inject


@pytest.fixture
def inject_test_services() -> Callable[[], Callable[[], AppServices]]:
    """Return the build_testing factory for full in-memory testing.

    For full service replacement with in-memory adapters. Use
    ``inject_config`` or ``email_cli_context`` for more granular control.

    Returns:
        Callable[[], Callable[[], AppServices]]: Function that returns the
            ``build_testing`` factory (in-memory adapters, no filesystem I/O).

    Example:
        def test_with_memory_services(
            cli_runner: CliRunner,
            inject_test_services: Callable[[], Callable[[], AppServices]],
        ) -> None:
            factory = inject_test_services()
            result = cli_runner.invoke(cli, ["config"], obj=factory)
            # Uses in-memory config, no disk access
    """
    from fake_winreg.composition import build_testing

    def _inject() -> Callable[[], AppServices]:
        return build_testing

    return _inject


@pytest.fixture
def config_cli_context(
    clear_config_cache: None,
) -> Callable[[dict[str, Any]], Callable[[], AppServices]]:
    """Create CLI test context with injected config.

    Combines config creation and injection into a single fixture.
    Simpler than ``inject_config`` when you don't need a pre-built Config object.

    Args:
        clear_config_cache: Implicit fixture dependency ensuring cache is cleared.

    Returns:
        Callable[[dict[str, Any]], Callable[[], AppServices]]: Function that takes
            a config dict and returns a services factory for CLI invocation.

    Example:
        def test_config_display(
            cli_runner: CliRunner,
            config_cli_context: Callable[[dict[str, Any]], Callable[[], AppServices]],
        ) -> None:
            factory = config_cli_context({"section": {"key": "value"}})
            result = cli_runner.invoke(cli, ["config"], obj=factory)
            assert "key" in result.output
    """
    from fake_winreg.composition import AppServices, build_production

    def _create(config_data: dict[str, Any]) -> Callable[[], AppServices]:
        config = Config(config_data, {})
        prod = build_production()

        def _fake_get_config(**_kwargs: Any) -> Config:
            return config

        test_services = AppServices(
            get_config=_fake_get_config,
            get_default_config_path=prod.get_default_config_path,
            deploy_configuration=prod.deploy_configuration,
            display_config=prod.display_config,
            init_logging=prod.init_logging,
        )
        return lambda: test_services

    return _create
