"""Conversation threads and the messages inside them."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Text, Uuid
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from docu.db.base import Base, SoftDelete, TenantMixin, Timestamps, UUIDPk

__all__ = ["Message", "Thread"]


class Thread(UUIDPk, Timestamps, SoftDelete, TenantMixin, Base):
    __tablename__ = "threads"
    __table_args__ = (
        Index("ix_threads_workspace_archived_created", "workspace_id", "archived", "created_at"),
    )

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    template_id: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text, default="")
    archived: Mapped[bool] = mapped_column(default=False)
    web_search: Mapped[bool] = mapped_column(default=False)
    checkpoint_ns: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class Message(UUIDPk, Timestamps, TenantMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("role in ('user', 'assistant', 'tool')", name="role"),
        Index("ix_messages_thread_created", "thread_id", "created_at"),
    )

    thread_id: Mapped[UUID] = mapped_column(ForeignKey("threads.id", ondelete="CASCADE"))
    turn_id: Mapped[UUID | None] = mapped_column()
    role: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text, default="")
    tool_name: Mapped[str | None] = mapped_column(Text)
    tool_args: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    tool_ok: Mapped[bool | None] = mapped_column()
    slide_ids: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    attachment_ids: Mapped[list[UUID]] = mapped_column(ARRAY(Uuid), default=list)
    blocks: Mapped[list[object] | None] = mapped_column(JSONB)
