"""Sessions, linked identities, and one-time auth tokens."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from docu.db.base import Base, Timestamps, UUIDPk

__all__ = ["AuthToken", "Identity", "Session"]


class Session(Base):
    """The primary key is the hash of the cookie value, not a UUIDv7."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ip: Mapped[str | None] = mapped_column(Text)
    user_agent: Mapped[str | None] = mapped_column(Text)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Identity(UUIDPk, Timestamps, Base):
    __tablename__ = "identities"
    __table_args__ = (
        UniqueConstraint("provider", "subject"),
        CheckConstraint("provider in ('google')", name="provider"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(Text)
    subject: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text)


class AuthToken(UUIDPk, Base):
    __tablename__ = "auth_tokens"
    __table_args__ = (CheckConstraint("kind in ('verify_email', 'password_reset')", name="kind"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(Text)
    token_hash: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
