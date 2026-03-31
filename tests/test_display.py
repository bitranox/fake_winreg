"""Integration tests for config display wrapper.

Tests the thin wrapper that delegates to lib_layered_config's display_config.
The wrapper adds log flushing before display. Core display behavior is tested
in lib_layered_config's test suite.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from lib_layered_config import Config
from lib_layered_config.domain.config import SourceInfo

from fake_winreg.adapters.config.display import display_config
from fake_winreg.domain.enums import OutputFormat

# ======================== display_config — error paths ========================


@pytest.mark.os_agnostic
def test_display_config_raises_for_nonexistent_section(
    config_factory: Callable[[dict[str, Any]], Config],
) -> None:
    """Requesting a section that doesn't exist must raise ValueError."""
    config = config_factory({"existing_section": {"key": "value"}})
    with pytest.raises(ValueError, match="not found"):
        display_config(config, output_format=OutputFormat.HUMAN, section="nonexistent")


@pytest.mark.os_agnostic
def test_display_config_raises_for_nonexistent_section_json(
    config_factory: Callable[[dict[str, Any]], Config],
) -> None:
    """Requesting a nonexistent section in JSON format must also raise ValueError."""
    config = config_factory({"existing_section": {"key": "value"}})
    with pytest.raises(ValueError, match="not found"):
        display_config(config, output_format=OutputFormat.JSON, section="nonexistent")


# ======================== display_config — wrapper integration ========================


@pytest.mark.os_agnostic
def test_display_human_renders_output(capsys: pytest.CaptureFixture[str]) -> None:
    """Wrapper must produce human-readable output via lib_layered_config."""
    config = Config({"app_name": "myapp", "section": {"key": "val"}}, {})
    display_config(config, output_format=OutputFormat.HUMAN)
    output = capsys.readouterr().out

    assert 'app_name = "myapp"' in output
    assert "[section]" in output


@pytest.mark.os_agnostic
def test_display_json_renders_output(capsys: pytest.CaptureFixture[str]) -> None:
    """Wrapper must produce JSON output via lib_layered_config."""
    config = Config({"section": {"key": "value"}}, {})
    display_config(config, output_format=OutputFormat.JSON)
    output = capsys.readouterr().out

    assert '"section"' in output
    assert '"key": "value"' in output


@pytest.mark.os_agnostic
def test_display_human_renders_profile_in_provenance(
    capsys: pytest.CaptureFixture[str],
    source_info_factory: Callable[..., SourceInfo],
) -> None:
    """Profile name must pass through to lib_layered_config."""
    metadata: dict[str, SourceInfo] = {
        "section.key": source_info_factory("section.key", "user", "/home/user/.config/app/config.toml"),
    }
    config = Config({"section": {"key": "value"}}, metadata)

    display_config(config, output_format=OutputFormat.HUMAN, profile="production")

    output = capsys.readouterr().out
    assert "# layer:user profile:production" in output


# ======================== Falsey value handling ========================


@pytest.mark.os_agnostic
def test_display_config_displays_section_with_zero_value(capsys: pytest.CaptureFixture[str]) -> None:
    """Section with integer zero value must display (not raise as 'not found')."""
    config = Config({"section": {"count": 0}}, {})

    display_config(config, output_format=OutputFormat.HUMAN, section="section")

    output = capsys.readouterr().out
    assert "count = 0" in output


@pytest.mark.os_agnostic
def test_display_config_displays_section_with_false_value(capsys: pytest.CaptureFixture[str]) -> None:
    """Section with boolean False value must display (not raise as 'not found')."""
    config = Config({"section": {"enabled": False}}, {})

    display_config(config, output_format=OutputFormat.HUMAN, section="section")

    output = capsys.readouterr().out
    # TOML uses lowercase 'false', not Python's 'False'
    assert "enabled = false" in output


@pytest.mark.os_agnostic
def test_display_config_json_displays_section_with_falsey_values(capsys: pytest.CaptureFixture[str]) -> None:
    """JSON format with falsey values must display (not raise as 'not found')."""
    config = Config({"section": {"count": 0, "enabled": False, "items": []}}, {})

    display_config(config, output_format=OutputFormat.JSON, section="section")

    output = capsys.readouterr().out
    assert '"count": 0' in output
    assert '"enabled": false' in output
    assert '"items": []' in output
