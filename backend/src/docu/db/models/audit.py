"""Workspace and platform audit events."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from docu.db.base import Base, UUIDPk

__all__ = ["AuditLog"]


class AuditLog(UUIDPk, Base):
    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_log_workspace_created", "workspace_id", "created_at"),)

    workspace_id: Mapped[UUID | None] = mapped_column(index=True)
    actor_id: Mapped[UUID | None] = mapped_column()
    action: Mapped[str] = mapped_column(Text)
    target_type: Mapped[str | None] = mapped_column(Text)
    target_id: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    ip: Mapped[str | None] = mapped_column(Text)
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
