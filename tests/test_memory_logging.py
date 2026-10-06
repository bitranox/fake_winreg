"""The testing composition's logging runtime, and the per-test reset of logging state.

Every command binds job context onto the process-global lib_log_rich runtime, so the
in-memory logging adapter must leave a live runtime behind or ``build_testing()`` cannot run
a single command. That runtime (and the root logger that production ``init_logging``
mutates) is process-global, so the suite restores both after every test; the
``isolated_logging_state`` fixture hands a test the same restore step so it can prove the
reset within one test instead of relying on test order.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import lib_log_rich.runtime
import pytest
from lib_layered_config import Config

from fake_winreg.adapters import cli as cli_mod
from fake_winreg.adapters.logging.setup import init_logging
from fake_winreg.composition import build_testing

if TYPE_CHECKING:
    from collections.abc import Callable

    from click.testing import CliRunner

    from fake_winreg.composition import AppServices


@pytest.mark.os_agnostic
@pytest.mark.parametrize("command", ["info", "config"])
def test_a_command_that_binds_runs_under_build_testing(cli_runner: CliRunner, command: str) -> None:
    """Each of these calls ``lib_log_rich.runtime.bind(...)``, which raises unless a runtime is live."""
    result = cli_runner.invoke(cli_mod.cli, [command], obj=build_testing)

    assert result.exception is None, result.exception
    assert result.exit_code == 0, result.output


@pytest.mark.os_agnostic
def test_the_reset_shuts_down_the_runtime_a_command_started(
    cli_runner: CliRunner, isolated_logging_state: Callable[[], None]
) -> None:
    result = cli_runner.invoke(cli_mod.cli, ["info"], obj=build_testing)
    assert result.exit_code == 0, result.output
    assert lib_log_rich.runtime.is_initialised() is True

    isolated_logging_state()

    assert lib_log_rich.runtime.is_initialised() is False


@pytest.mark.os_agnostic
def test_the_reset_restores_the_root_logger_a_production_init_changed(
    isolated_logging_state: Callable[[], None],
) -> None:
    """Production ``init_logging`` attaches a stdlib handler to the root logger and raises its
    level; ``runtime.shutdown()`` undoes neither, so the reset must, or a later test's stdlib
    warnings are swallowed depending on which test ran first."""
    root = logging.getLogger()
    before = (list(root.handlers), root.level, root.propagate)

    init_logging(Config({}, {}))
    assert (list(root.handlers), root.level, root.propagate) != before

    isolated_logging_state()

    assert (list(root.handlers), root.level, root.propagate) == before


def _deploy_nothing(**_kwargs: Any) -> list[Path]:
    return []


#: Each services-building fixture, with how to get one AppServices out of it.
_SERVICE_FIXTURES: dict[str, Callable[[Any], AppServices]] = {
    "inject_config": lambda make: make(Config({}, {}))(),
    "inject_config_with_profile_capture": lambda make: make(Config({}, {}), [])(),
    "inject_deploy_with_profile_capture": lambda make: make(Path("config.toml"), [])(),
    "inject_deploy_configuration": lambda make: make(_deploy_nothing)(),
    "config_cli_context": lambda make: make({})(),
}


@pytest.mark.os_agnostic
@pytest.mark.parametrize("fixture_name", _SERVICE_FIXTURES)
def test_the_service_fixtures_log_through_the_quiet_runtime(request: pytest.FixtureRequest, fixture_name: str) -> None:
    """Production ``init_logging`` queues INFO lines that race into CliRunner's stderr, so a
    test asserting on stderr would pass or fail by timing; the fixtures use the testing one."""
    services = _SERVICE_FIXTURES[fixture_name](request.getfixturevalue(fixture_name))

    assert services.init_logging is build_testing().init_logging
