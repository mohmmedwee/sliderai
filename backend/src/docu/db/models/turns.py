"""Agent turns and the questions they are waiting on."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from docu.db.base import Base, TenantMixin, Timestamps, UUIDPk

__all__ = ["PendingInput", "Turn"]


class Turn(UUIDPk, Timestamps, TenantMixin, Base):
    __tablename__ = "turns"
    __table_args__ = (
        CheckConstraint(
            "status in ('queued','running','waiting_input','committed',"
            "'failed','cancelled','rejected')",
            name="status",
        ),
        CheckConstraint(
            "profile in ('deck','document','webpage','social','import','assistant')",
            name="profile",
        ),
        CheckConstraint("effort in ('fast','standard','deep')", name="effort"),
    )

    thread_id: Mapped[UUID] = mapped_column(ForeignKey("threads.id", ondelete="CASCADE"))
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(Text)
    base_version: Mapped[int] = mapped_column(Integer)
    committed_version: Mapped[int | None] = mapped_column(Integer)
    model: Mapped[str] = mapped_column(Text)
    fallback_used: Mapped[bool] = mapped_column(default=False)
    profile: Mapped[str] = mapped_column(Text)
    effort: Mapped[str] = mapped_column(Text)
    prompt_version_id: Mapped[UUID] = mapped_column(ForeignKey("prompt_versions.id"))
    skill: Mapped[str | None] = mapped_column(Text)
    web_search: Mapped[bool] = mapped_column(default=False)
    steps: Mapped[int] = mapped_column(Integer, default=0)
    max_steps: Mapped[int] = mapped_column(Integer)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    ttft_ms: Mapped[int] = mapped_column(Integer, default=0)
    langsmith_run_id: Mapped[UUID | None] = mapped_column()
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cached_tokens: Mapped[int] = mapped_column(Integer, default=0)
    reasoning_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=0)
    credits_reserved: Mapped[int] = mapped_column(Integer, default=0)
    credits_charged: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PendingInput(UUIDPk, Timestamps, TenantMixin, Base):
    __tablename__ = "pending_inputs"
    __table_args__ = (
        UniqueConstraint("turn_id", "tool_call_id"),
        CheckConstraint("kind in ('approval', 'ask_user')", name="kind"),
    )

    turn_id: Mapped[UUID] = mapped_column(ForeignKey("turns.id", ondelete="CASCADE"))
    tool_call_id: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    answer: Mapped[dict[str, object] | None] = mapped_column(JSONB)
