"""Skill catalog settings face."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

__all__ = ["SKILLS_FLAT", "SkillsSettings"]


class SkillsSettings(BaseModel):
    """Which skills load and how large a body may be."""

    dirs: list[Path] = Field(
        default_factory=lambda: [
            Path.home() / ".agents" / "skills",
            Path.home() / ".cursor" / "skills",
            Path("skills"),
        ],
    )
    allowlist: set[str] = Field(
        default_factory=lambda: {
            "answering-well",
            "planning-with-intention",
            "research",
            "working-with-documents",
            "file-reading",
            "writing-deliverables",
            "replying-bilingually",
            "diagnosing-problems",
            "memory",
            "grilling",
            "teach",
            "to-questionnaire",
            "writing-guidelines",
            "writing-shape",
            "writing-fragments",
            "writing-beats",
            "doc-coauthoring",
            "theme-factory",
            "brand-guidelines",
            "internal-comms",
            "canvas-design",
            "generate-image",
            "skill-creator",
        },
    )
    max_chars: int = Field(default=24_000, gt=0)
    max_user_skills: int = Field(default=20, gt=0)
    max_user_skill_body_chars: int = Field(default=12_000, gt=0)


SKILLS_FLAT: dict[str, str] = {
    "skill_dirs": "dirs",
    "skill_allowlist": "allowlist",
    "max_skill_chars": "max_chars",
    "max_user_skills": "max_user_skills",
    "max_user_skill_body_chars": "max_user_skill_body_chars",
}
