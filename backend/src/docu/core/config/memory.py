"""Durable user-memory settings face."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["MEMORY_FLAT", "MemorySettings"]


class MemorySettings(BaseModel):
    """Caps on per-account memory notes."""

    max_items: int = Field(default=50, gt=0)
    max_chars: int = Field(default=400, gt=0)


MEMORY_FLAT: dict[str, str] = {
    "max_memory_items": "max_items",
    "max_memory_chars": "max_chars",
}
