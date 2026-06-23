"""Domain enum tests: member values, string equality, and exhaustive member counts."""

from __future__ import annotations

import pytest

from fake_winreg.domain.enums import DeployTarget, OutputFormat

# ======================== OutputFormat ========================


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    ("member", "expected_value"),
    [
        (OutputFormat.HUMAN, "human"),
        (OutputFormat.JSON, "json"),
    ],
)
def test_output_format_member_values(member: OutputFormat, expected_value: str) -> None:
    """Each OutputFormat member must have the expected string value."""
    assert member.value == expected_value


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    ("member", "expected_str"),
    [
        (OutputFormat.HUMAN, "human"),
        (OutputFormat.JSON, "json"),
    ],
)
def test_output_format_string_equality(member: OutputFormat, expected_str: str) -> None:
    """OutputFormat members must compare equal to their plain string equivalents."""
    assert member == expected_str


@pytest.mark.os_agnostic
def test_output_format_member_count() -> None:
    """OutputFormat must have exactly 2 members."""
    assert len(OutputFormat) == 2


# ======================== DeployTarget ========================


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    ("member", "expected_value"),
    [
        (DeployTarget.APP, "app"),
        (DeployTarget.HOST, "host"),
        (DeployTarget.USER, "user"),
    ],
)
def test_deploy_target_member_values(member: DeployTarget, expected_value: str) -> None:
    """Each DeployTarget member must have the expected string value."""
    assert member.value == expected_value


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    ("member", "expected_str"),
    [
        (DeployTarget.APP, "app"),
        (DeployTarget.HOST, "host"),
        (DeployTarget.USER, "user"),
    ],
)
def test_deploy_target_string_equality(member: DeployTarget, expected_str: str) -> None:
    """DeployTarget members must compare equal to their plain string equivalents."""
    assert member == expected_str


@pytest.mark.os_agnostic
def test_deploy_target_member_count() -> None:
    """DeployTarget must have exactly 3 members."""
    assert len(DeployTarget) == 3
