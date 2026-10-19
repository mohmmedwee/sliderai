"""Test double switch for the chat model."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["FAKE_FLAT", "FakeSettings"]


class FakeSettings(BaseModel):
    """When set, model calls use the scripted fake and UPSTREAM is optional."""

    agent_fake_model: bool = Field(default=False)


FAKE_FLAT: dict[str, str] = {
    "agent_fake_model": "agent_fake_model",
}
