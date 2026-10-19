"""System and workspace themes and templates."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from docu.db.base import Base, Timestamps

__all__ = ["Template", "Theme"]


class Theme(Timestamps, Base):
    __tablename__ = "themes"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    workspace_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(Text)
    tokens: Mapped[dict[str, object]] = mapped_column(JSONB)


class Template(Timestamps, Base):
    __tablename__ = "templates"
    __table_args__ = (
        CheckConstraint(
            "category in ('pitch','report','education','marketing','event','planning','personal')",
            name="category",
        ),
        CheckConstraint(
            "format in ('presentation','document','webpage','social')",
            name="format",
        ),
        CheckConstraint("lang in ('en','ar')", name="lang"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    workspace_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE")
    )
    name_en: Mapped[str] = mapped_column(Text)
    name_ar: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Text)
    format: Mapped[str] = mapped_column(Text)
    theme_id: Mapped[str] = mapped_column(ForeignKey("themes.id"))
    colors: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    lang: Mapped[str] = mapped_column(Text)
    cards: Mapped[list[object]] = mapped_column(JSONB)
