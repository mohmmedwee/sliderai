"""Shared repository types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Page[T]:
    items: list[T]
    next_cursor: str | None


__all__ = ["Page"]
