"""Documents, immutable revisions, and outside-workspace access."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from docu.db.base import Base, SoftDelete, TenantMixin, Timestamps, UUIDPk

__all__ = ["Document", "DocumentAccess", "DocumentRevision"]


class Document(UUIDPk, Timestamps, SoftDelete, TenantMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "format in ('presentation', 'document', 'webpage', 'social')",
            name="format",
        ),
        CheckConstraint("visibility in ('private', 'workspace')", name="visibility"),
        Index(
            "ix_documents_workspace_updated",
            "workspace_id",
            text("updated_at desc"),
            postgresql_where=text("deleted_at is null"),
        ),
    )

    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(Text)
    format: Mapped[str] = mapped_column(Text)
    theme_id: Mapped[str] = mapped_column(ForeignKey("themes.id"))
    content: Mapped[dict[str, object]] = mapped_column(JSONB)
    version: Mapped[int] = mapped_column(Integer, default=1)
    visibility: Mapped[str] = mapped_column(Text)
    active_turn_id: Mapped[UUID | None] = mapped_column()
    manual_edits_since_agent: Mapped[int] = mapped_column(Integer, default=0)
    thumbnail_asset_id: Mapped[UUID | None] = mapped_column()


class DocumentRevision(UUIDPk, Timestamps, TenantMixin, Base):
    __tablename__ = "document_revisions"
    __table_args__ = (
        UniqueConstraint("document_id", "version"),
        CheckConstraint("source in ('agent_turn', 'manual', 'restore', 'theme')", name="source"),
    )

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer)
    content: Mapped[dict[str, object]] = mapped_column(JSONB)
    title: Mapped[str] = mapped_column(Text)
    theme_id: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)
    turn_id: Mapped[UUID | None] = mapped_column()
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class DocumentAccess(UUIDPk, Timestamps, TenantMixin, Base):
    __tablename__ = "document_access"
    __table_args__ = (
        UniqueConstraint("document_id", "user_id"),
        CheckConstraint("role in ('view', 'edit')", name="role"),
    )

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(Text)
