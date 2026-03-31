"""Profile validation tests.

Tests profile name validation using lib_layered_config.validate_profile_name().
Validates length limits, character restrictions, Windows reserved names, and
path traversal prevention.
"""

from __future__ import annotations

import pytest


@pytest.mark.os_agnostic
def test_when_profile_contains_path_traversal_it_rejects(clear_config_cache: None) -> None:
    """Profile names containing path traversal sequences must be rejected."""
    from fake_winreg.adapters.config.loader import get_config

    with pytest.raises(ValueError, match=r"profile.*invalid|invalid.*profile"):
        get_config(profile="../etc")


@pytest.mark.os_agnostic
def test_when_profile_is_dot_dot_it_rejects(clear_config_cache: None) -> None:
    """A bare '..' profile must be rejected."""
    from fake_winreg.adapters.config.loader import get_config

    with pytest.raises(ValueError, match="profile"):
        get_config(profile="..")


@pytest.mark.os_agnostic
def test_when_profile_contains_slash_it_rejects(clear_config_cache: None) -> None:
    """Profile names with slashes must be rejected."""
    from fake_winreg.adapters.config.loader import get_config

    with pytest.raises(ValueError, match=r"profile.*invalid|invalid.*profile"):
        get_config(profile="foo/bar")


@pytest.mark.os_agnostic
def test_when_profile_is_valid_alphanumeric_it_accepts(clear_config_cache: None) -> None:
    """Alphanumeric profiles with hyphens and underscores must be accepted."""
    from fake_winreg.adapters.config.loader import get_config

    # Should not raise — the config may or may not exist, but validation passes
    config = get_config(profile="staging-v2")
    assert config is not None


@pytest.mark.os_agnostic
def test_when_deploy_receives_invalid_profile_it_rejects(monkeypatch: pytest.MonkeyPatch) -> None:
    """deploy_configuration must reject path traversal profiles."""
    from fake_winreg.adapters.config.deploy import deploy_configuration
    from fake_winreg.domain.enums import DeployTarget

    with pytest.raises(ValueError, match=r"profile.*invalid|invalid.*profile"):
        deploy_configuration(targets=[DeployTarget.USER], profile="../../x")


# --------------------------------------------------------------------------
# lib_layered_config integration tests
# --------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_when_profile_exceeds_max_length_it_rejects(clear_config_cache: None) -> None:
    """Profile names exceeding 64 characters must be rejected."""
    from fake_winreg.adapters.config.loader import validate_profile

    long_profile = "a" * 65
    with pytest.raises(ValueError, match=r"[Ii]nvalid profile|too long|length"):
        validate_profile(long_profile)


@pytest.mark.os_agnostic
def test_when_profile_is_exactly_max_length_it_accepts(clear_config_cache: None) -> None:
    """Profile names at exactly 64 characters must be accepted."""
    from fake_winreg.adapters.config.loader import validate_profile

    max_profile = "a" * 64
    # Should not raise
    validate_profile(max_profile)


@pytest.mark.os_agnostic
def test_when_profile_is_empty_string_it_rejects(clear_config_cache: None) -> None:
    """Empty profile names must be rejected."""
    from fake_winreg.adapters.config.loader import validate_profile

    with pytest.raises(ValueError, match=r"[Ii]nvalid profile|empty|cannot be empty"):
        validate_profile("")


@pytest.mark.os_agnostic
@pytest.mark.parametrize("reserved_name", ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"])
def test_when_profile_is_windows_reserved_name_it_rejects(reserved_name: str, clear_config_cache: None) -> None:
    """Windows reserved names must be rejected for cross-platform safety."""
    from fake_winreg.adapters.config.loader import validate_profile

    with pytest.raises(ValueError, match=r"[Ii]nvalid profile|reserved"):
        validate_profile(reserved_name)


@pytest.mark.os_agnostic
def test_when_profile_starts_with_hyphen_it_rejects(clear_config_cache: None) -> None:
    """Profile names starting with hyphen must be rejected."""
    from fake_winreg.adapters.config.loader import validate_profile

    with pytest.raises(ValueError, match=r"[Ii]nvalid profile|start"):
        validate_profile("-invalid")


@pytest.mark.os_agnostic
def test_when_profile_starts_with_underscore_it_rejects(clear_config_cache: None) -> None:
    """Profile names starting with underscore must be rejected."""
    from fake_winreg.adapters.config.loader import validate_profile

    with pytest.raises(ValueError, match=r"[Ii]nvalid profile|start"):
        validate_profile("_invalid")


@pytest.mark.os_agnostic
def test_validate_profile_accepts_custom_max_length(clear_config_cache: None) -> None:
    """validate_profile accepts optional max_length parameter."""
    from fake_winreg.adapters.config.loader import validate_profile

    # Valid at custom length 10
    validate_profile("abcdefghij", max_length=10)

    # Invalid at custom length 10
    with pytest.raises(ValueError):
        validate_profile("abcdefghijk", max_length=10)
