"""Prompt versions and the single platform settings row."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from docu.db.base import Base, UUIDPk

__all__ = ["PlatformSettings", "PromptVersion"]


class PromptVersion(UUIDPk, Base):
    __tablename__ = "prompt_versions"
    __table_args__ = (
        Index(
            "uq_prompt_versions_one_active",
            "name",
            unique=True,
            postgresql_where=text("is_active"),
        ),
    )

    name: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(default=False)


class PlatformSettings(Base):
    __tablename__ = "platform_settings"
    __table_args__ = (CheckConstraint("id = 1", name="singleton"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    data: Mapped[dict[str, object]] = mapped_column(JSONB)
