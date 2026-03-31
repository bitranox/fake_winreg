"""Property-based tests for CLI configuration overrides.

Uses hypothesis to generate arbitrary inputs and verify that
``parse_override`` and ``coerce_value`` satisfy their contracts
for all representable strings, not just hand-picked examples.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fake_winreg.adapters.config.overrides import (
    coerce_value,
    parse_override,
)

# ======================== coerce_value property tests ========================

ALLOWED_COERCED_TYPES = (str, int, float, bool, type(None), list, dict)


@pytest.mark.os_agnostic
@given(raw=st.text())
@settings(max_examples=200)
def test_coerce_value_always_returns_valid_python_type(raw: str) -> None:
    """coerce_value never raises and always returns str, int, float, bool, None, list, or dict."""
    result = coerce_value(raw)

    assert isinstance(result, ALLOWED_COERCED_TYPES) or result is None


@pytest.mark.os_agnostic
@given(raw=st.text(min_size=0, max_size=0))
def test_coerce_value_empty_string_returns_empty_string(raw: str) -> None:
    """Empty string input always yields empty string output."""
    assert coerce_value(raw) == ""


@pytest.mark.os_agnostic
@given(value=st.integers(min_value=-(2**53), max_value=2**53))
def test_coerce_value_round_trips_integers(value: int) -> None:
    """Integer values survive a str -> coerce_value round-trip."""
    assert coerce_value(str(value)) == value


@pytest.mark.os_agnostic
@given(value=st.booleans())
def test_coerce_value_round_trips_booleans(value: bool) -> None:
    """Boolean values survive a JSON-string -> coerce_value round-trip."""
    json_str = "true" if value else "false"

    assert coerce_value(json_str) is value


@pytest.mark.os_agnostic
@given(raw=st.from_regex(r"[A-Za-z_][A-Za-z0-9_]*", fullmatch=True))
@settings(max_examples=200)
def test_coerce_value_identifier_strings_return_as_string(raw: str) -> None:
    """Identifier-like strings that are not JSON keywords fall back to raw string."""
    if raw in ("true", "false", "null"):
        return  # These are valid JSON literals; skip them

    result = coerce_value(raw)

    assert result == raw
    assert isinstance(result, str)


# ======================== parse_override property tests ========================


@pytest.mark.os_agnostic
@given(
    section=st.from_regex(r"[A-Za-z_][A-Za-z0-9_]*", fullmatch=True),
    key=st.from_regex(r"[A-Za-z_][A-Za-z0-9_]*", fullmatch=True),
    value=st.text(min_size=0, max_size=50),
)
@settings(max_examples=200)
def test_parse_override_valid_inputs_parse_without_error(section: str, key: str, value: str) -> None:
    """Any well-formed SECTION.KEY=VALUE string parses successfully."""
    raw = f"{section}.{key}={value}"

    result = parse_override(raw)

    assert result.section == section
    assert result.key_path == (key,)
    assert result.value == coerce_value(value)


@pytest.mark.os_agnostic
@given(
    section=st.from_regex(r"[A-Za-z_][A-Za-z0-9_]*", fullmatch=True),
    key1=st.from_regex(r"[A-Za-z_][A-Za-z0-9_]*", fullmatch=True),
    key2=st.from_regex(r"[A-Za-z_][A-Za-z0-9_]*", fullmatch=True),
    value=st.text(min_size=0, max_size=50),
)
@settings(max_examples=200)
def test_parse_override_nested_keys_produce_correct_key_path(
    section: str,
    key1: str,
    key2: str,
    value: str,
) -> None:
    """Nested SECTION.KEY1.KEY2=VALUE parses into a two-element key_path tuple."""
    raw = f"{section}.{key1}.{key2}={value}"

    result = parse_override(raw)

    assert result.section == section
    assert result.key_path == (key1, key2)


@pytest.mark.os_agnostic
@given(raw=st.text().filter(lambda s: "=" not in s))
@settings(max_examples=200)
def test_parse_override_rejects_strings_without_equals(raw: str) -> None:
    """Any string lacking '=' is rejected with ValueError."""
    with pytest.raises(ValueError, match="must contain '='"):
        parse_override(raw)


@pytest.mark.os_agnostic
@given(
    key_part=st.text(min_size=1).filter(lambda s: "." not in s and "=" not in s),
    value=st.text(min_size=0, max_size=20),
)
@settings(max_examples=200)
def test_parse_override_rejects_strings_without_dot_in_key(key_part: str, value: str) -> None:
    """Any KEY=VALUE where KEY has no dot is rejected with ValueError."""
    raw = f"{key_part}={value}"

    with pytest.raises(ValueError, match="must contain at least one dot"):
        parse_override(raw)


@pytest.mark.os_agnostic
@given(
    section=st.from_regex(r"[A-Za-z_][A-Za-z0-9_]*", fullmatch=True),
    key=st.from_regex(r"[A-Za-z_][A-Za-z0-9_]*", fullmatch=True),
    value=st.text(min_size=0, max_size=50),
)
@settings(max_examples=200)
def test_parse_override_section_equals_first_dotted_component(section: str, key: str, value: str) -> None:
    """The section field always matches the substring before the first dot."""
    raw = f"{section}.{key}={value}"

    result = parse_override(raw)

    assert result.section == section


@pytest.mark.os_agnostic
@given(
    section=st.from_regex(r"[A-Za-z_][A-Za-z0-9_]*", fullmatch=True),
    key=st.from_regex(r"[A-Za-z_][A-Za-z0-9_]*", fullmatch=True),
)
def test_parse_override_preserves_equals_in_value(section: str, key: str) -> None:
    """Value portion containing '=' is preserved intact (split on first '=' only)."""
    raw = f"{section}.{key}=val=ue"

    result = parse_override(raw)

    assert result.value == "val=ue"
