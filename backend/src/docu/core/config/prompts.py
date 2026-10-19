"""System prompt template settings face."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

__all__ = ["PROMPTS_FLAT", "PromptsSettings"]


class PromptsSettings(BaseModel):
    """Where prompt Markdown lives."""

    dir: Path = Field(default=Path("prompts"))
    system_prompt: str | None = Field(default=None)


PROMPTS_FLAT: dict[str, str] = {
    "prompt_dir": "dir",
    "system_prompt": "system_prompt",
}
