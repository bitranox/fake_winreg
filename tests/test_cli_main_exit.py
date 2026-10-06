"""Exit codes and stderr through the real ``main()`` entry point.

``CliRunner.invoke(cli, ...)`` calls the click command tree directly and never runs
``main()``'s ``standalone_mode=False`` handling, which is where a bare ``SystemExit`` from a
command falls into the catch-all branch and is printed to stderr as ``SystemExit: N`` - text
a user reads as a crash. These tests go through ``main()`` itself, as a console script does,
with the services replaced at the composition seam.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any

import click
import pytest
from lib_layered_config import Config

from fake_winreg.adapters.cli.main import main
from fake_winreg.composition import AppServices, build_testing

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def _services(data: dict[str, Any], **overrides: Any) -> Callable[[], AppServices]:
    config = Config(data, {})

    def get_config(**_kwargs: Any) -> Config:
        return config

    def build() -> AppServices:
        return dataclasses.replace(build_testing(), get_config=get_config, **overrides)

    return build


def _raising(error: Exception) -> Callable[..., Any]:
    def raise_it(*_args: Any, **_kwargs: Any) -> Any:
        raise error

    return raise_it


@pytest.mark.os_agnostic
def test_a_config_display_error_exits_22_without_printing_systemexit(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["config"], services_factory=_services({}, display_config=_raising(ValueError("boom"))))

    err = capsys.readouterr().err
    assert exit_code == 22
    assert "boom" in err
    assert "SystemExit" not in err


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    ("error", "expected"),
    [(PermissionError("denied"), 13), (OSError("disk full"), 1)],
    ids=["permission-denied", "general-error"],
)
def test_a_deploy_failure_exits_with_its_code_without_printing_systemexit(
    capsys: pytest.CaptureFixture[str], error: Exception, expected: int
) -> None:
    services = _services({}, deploy_configuration=_raising(error))
    exit_code = main(["config-deploy", "--target", "user"], services_factory=services)

    err = capsys.readouterr().err
    assert exit_code == expected
    assert str(error) in err
    assert "SystemExit" not in err


@pytest.mark.os_agnostic
def test_a_deliberate_exit_inside_deploy_keeps_its_own_code(capsys: pytest.CaptureFixture[str]) -> None:
    """click's Exit is a RuntimeError; the deploy failure branch must let it through unrelabelled."""
    services = _services({}, deploy_configuration=_raising(click.exceptions.Exit(78)))
    exit_code = main(["config-deploy", "--target", "user"], services_factory=services)

    err = capsys.readouterr().err
    assert exit_code == 78
    assert "Failed to deploy configuration" not in err


@pytest.mark.os_agnostic
def test_a_generate_examples_failure_exits_1_without_printing_systemexit(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    blocker = tmp_path / "a-file"
    blocker.write_text("not a directory", encoding="utf-8")

    exit_code = main(
        ["config-generate-examples", "--destination", str(blocker / "sub")], services_factory=_services({})
    )

    err = capsys.readouterr().err
    assert exit_code == 1
    assert "Error:" in err
    assert "SystemExit" not in err


@pytest.mark.os_agnostic
def test_a_successful_command_exits_0(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["info"], services_factory=_services({}))

    assert exit_code == 0
    assert "fake_winreg" in capsys.readouterr().out
