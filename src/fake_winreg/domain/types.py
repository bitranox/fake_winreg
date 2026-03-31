"""Domain type definitions for registry value data."""

from __future__ import annotations

RegData = None | bytes | int | str | list[str]
"""All possible types of data that registry values can hold."""

__all__ = ["RegData"]
