"""Unit tests for CLI configuration overrides (--set SECTION.KEY=VALUE).

Tests cover parsing, value coercion, nest-override mechanics, and full
apply_overrides integration with the Config class.
"""

from __future__ import annotations

from typing import Any

import pytest
from lib_layered_config import Config

from fake_winreg.adapters.config.overrides import (
    ConfigOverride,
    apply_overrides,
    coerce_value,
    parse_override,
)

# ======================== parse_override tests ========================


@pytest.mark.os_agnostic
def test_parse_override_simple_key() -> None:
    """Simple SECTION.KEY=VALUE produces correct section and single-element key_path."""
    result = parse_override("lib_log_rich.console_level=DEBUG")

    assert result == ConfigOverride(section="lib_log_rich", key_path=("console_level",), value="DEBUG")


@pytest.mark.os_agnostic
def test_parse_override_nested_key() -> None:
    """Dotted key path beyond section creates multi-element key_path."""
    result = parse_override("lib_log_rich.payload_limits.message_max_chars=8192")

    assert result.section == "lib_log_rich"
    assert result.key_path == ("payload_limits", "message_max_chars")
    assert result.value == 8192


@pytest.mark.os_agnostic
def test_parse_override_value_containing_equals() -> None:
    """Value containing '=' is preserved intact after the first split."""
    result = parse_override("section.key=val=ue")

    assert result.value == "val=ue"


@pytest.mark.os_agnostic
def test_parse_override_empty_value() -> None:
    """Empty value after '=' produces empty string."""
    result = parse_override("section.key=")

    assert result.value == ""


@pytest.mark.os_agnostic
def test_parse_override_rejects_missing_equals() -> None:
    """Override without '=' raises ValueError."""
    with pytest.raises(ValueError, match="must contain '='"):
        parse_override("section.key_no_equals")


@pytest.mark.os_agnostic
def test_parse_override_rejects_no_dot_in_key() -> None:
    """Override without dot in key part raises ValueError."""
    with pytest.raises(ValueError, match="must contain at least one dot"):
        parse_override("sectiononly=value")


@pytest.mark.os_agnostic
def test_parse_override_rejects_empty_section() -> None:
    """Leading dot produces empty section, which is rejected."""
    with pytest.raises(ValueError, match="section name is empty"):
        parse_override(".key=value")


@pytest.mark.os_agnostic
def test_parse_override_rejects_empty_key_component() -> None:
    """Double dot in key path produces empty component, which is rejected."""
    with pytest.raises(ValueError, match="empty component"):
        parse_override("section..key=value")


@pytest.mark.os_agnostic
def test_parse_override_rejects_trailing_dot_in_key() -> None:
    """Trailing dot produces empty final key component."""
    with pytest.raises(ValueError, match="empty component"):
        parse_override("section.key.=value")


@pytest.mark.os_agnostic
def test_parse_override_rejects_equals_only() -> None:
    """Bare '=value' with no dot in key part raises ValueError."""
    with pytest.raises(ValueError, match="must contain at least one dot"):
        parse_override("=value")


@pytest.mark.os_agnostic
def test_parse_override_rejects_bare_equals() -> None:
    """Bare '=' with empty everything raises ValueError."""
    with pytest.raises(ValueError, match="must contain at least one dot"):
        parse_override("=")


# ======================== coerce_value tests ========================


@pytest.mark.os_agnostic
def test_coerce_value_true() -> None:
    """JSON 'true' coerces to Python True."""
    assert coerce_value("true") is True


@pytest.mark.os_agnostic
def test_coerce_value_false() -> None:
    """JSON 'false' coerces to Python False."""
    assert coerce_value("false") is False


@pytest.mark.os_agnostic
def test_coerce_value_integer() -> None:
    """Numeric string coerces to int."""
    assert coerce_value("42") == 42
    assert isinstance(coerce_value("42"), int)


@pytest.mark.os_agnostic
def test_coerce_value_float() -> None:
    """Decimal numeric string coerces to float."""
    result = coerce_value("3.14")
    assert result == 3.14
    assert isinstance(result, float)


@pytest.mark.os_agnostic
def test_coerce_value_null() -> None:
    """JSON 'null' coerces to Python None."""
    assert coerce_value("null") is None


@pytest.mark.os_agnostic
def test_coerce_value_json_array() -> None:
    """JSON array string coerces to list."""
    assert coerce_value('["a","b"]') == ["a", "b"]


@pytest.mark.os_agnostic
def test_coerce_value_json_object() -> None:
    """JSON object string coerces to dict."""
    assert coerce_value('{"k":"v"}') == {"k": "v"}


@pytest.mark.os_agnostic
def test_coerce_value_plain_string() -> None:
    """Non-JSON string falls back to raw string."""
    assert coerce_value("DEBUG") == "DEBUG"


@pytest.mark.os_agnostic
def test_coerce_value_empty_string() -> None:
    """Empty string returns empty string."""
    assert coerce_value("") == ""


@pytest.mark.os_agnostic
def test_coerce_value_negative_number() -> None:
    """Negative number coerces correctly."""
    assert coerce_value("-5") == -5


@pytest.mark.os_agnostic
def test_coerce_value_unicode_string() -> None:
    """Unicode string falls back to raw string."""
    assert coerce_value("日本語") == "日本語"


@pytest.mark.os_agnostic
def test_coerce_value_string_with_spaces() -> None:
    """String containing spaces falls back to raw string."""
    assert coerce_value("hello world") == "hello world"


@pytest.mark.os_agnostic
def test_coerce_value_negative_float() -> None:
    """Negative float coerces correctly."""
    result = coerce_value("-3.14")
    assert result == -3.14
    assert isinstance(result, float)


@pytest.mark.os_agnostic
def test_coerce_value_scientific_notation() -> None:
    """Scientific notation coerces to float."""
    result = coerce_value("1e10")
    assert result == 1e10


@pytest.mark.os_agnostic
def test_parse_override_deeply_nested_key() -> None:
    """Three-level nesting produces correct key_path."""
    result = parse_override("s.a.b.c=42")

    assert result.section == "s"
    assert result.key_path == ("a", "b", "c")
    assert result.value == 42


@pytest.mark.os_agnostic
def test_parse_override_unicode_value() -> None:
    """Unicode characters in the value are preserved."""
    result = parse_override("s.key=こんにちは")

    assert result.value == "こんにちは"


@pytest.mark.os_agnostic
def test_parse_override_value_with_newline_json() -> None:
    """JSON string with escaped newline is parsed by orjson as a real newline."""
    result = parse_override('s.key="line1\\nline2"')

    assert result.value == "line1\nline2"


# ======================== apply_overrides tests ========================


def _make_config(data: dict[str, Any]) -> Config:
    """Create a minimal Config instance from a data dict for testing."""
    meta: dict[str, Any] = {}
    return Config(data, meta)


@pytest.mark.os_agnostic
def test_apply_overrides_empty_tuple_returns_same_instance() -> None:
    """No overrides returns the original Config instance unchanged."""
    config = _make_config({"s": {"k": 1}})

    result = apply_overrides(config, ())

    assert result is config


@pytest.mark.os_agnostic
def test_apply_overrides_single_override() -> None:
    """Single override sets the value in the correct section."""
    config = _make_config({"s": {"k": 1, "other": "kept"}})

    result = apply_overrides(config, ("s.k=2",))

    assert result["s"]["k"] == 2
    assert result["s"]["other"] == "kept"


@pytest.mark.os_agnostic
def test_apply_overrides_nested_key() -> None:
    """Nested key override creates intermediate dicts."""
    config = _make_config({"s": {"existing": "kept"}})

    result = apply_overrides(config, ("s.nested.deep=42",))

    assert result["s"]["nested"]["deep"] == 42
    assert result["s"]["existing"] == "kept"


@pytest.mark.os_agnostic
def test_apply_overrides_multiple_overrides() -> None:
    """Multiple overrides all apply to the result."""
    config = _make_config({"s": {"a": 1, "b": 2}})

    result = apply_overrides(config, ("s.a=10", "s.b=20"))

    assert result["s"]["a"] == 10
    assert result["s"]["b"] == 20


@pytest.mark.os_agnostic
def test_apply_overrides_preserves_unmodified_sections() -> None:
    """Sections not targeted by overrides remain unchanged."""
    config = _make_config({"s1": {"k": "original"}, "s2": {"k": "untouched"}})

    result = apply_overrides(config, ("s1.k=changed",))

    assert result["s1"]["k"] == "changed"
    assert result["s2"]["k"] == "untouched"


@pytest.mark.os_agnostic
def test_apply_overrides_creates_missing_section() -> None:
    """Override targeting a non-existent section creates it."""
    config = _make_config({"existing": {"k": 1}})

    result = apply_overrides(config, ("new_section.key=value",))

    assert result["new_section"]["key"] == "value"
    assert result["existing"]["k"] == 1


@pytest.mark.os_agnostic
def test_apply_overrides_boolean_coercion() -> None:
    """Boolean values are correctly coerced from JSON strings."""
    config = _make_config({"s": {"flag": False}})

    result = apply_overrides(config, ("s.flag=true",))

    assert result["s"]["flag"] is True


@pytest.mark.os_agnostic
def test_apply_overrides_does_not_mutate_original() -> None:
    """Original config is not modified by apply_overrides."""
    config = _make_config({"s": {"k": "original"}})

    result = apply_overrides(config, ("s.k=changed",))

    assert config["s"]["k"] == "original"
    assert result["s"]["k"] == "changed"


@pytest.mark.os_agnostic
def test_apply_overrides_rejects_malformed_input() -> None:
    """Malformed override string raises ValueError."""
    config = _make_config({"s": {"k": 1}})

    with pytest.raises(ValueError, match="must contain '='"):
        apply_overrides(config, ("invalid",))
