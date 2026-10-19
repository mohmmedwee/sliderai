"""User accounts."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, LargeBinary, Text
from sqlalchemy.dialects.postgresql import CITEXT, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from docu.db.base import Base, SoftDelete, Timestamps, UUIDPk

__all__ = ["User"]


class User(UUIDPk, Timestamps, SoftDelete, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("locale in ('en', 'ar')", name="locale"),
        CheckConstraint("digits in ('latn', 'arab')", name="digits"),
    )

    email: Mapped[str] = mapped_column(CITEXT, unique=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    password_hash: Mapped[str | None] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)
    image: Mapped[str | None] = mapped_column(Text)
    locale: Mapped[str] = mapped_column(Text)
    digits: Mapped[str] = mapped_column(Text)
    totp_secret_sealed: Mapped[bytes | None] = mapped_column(LargeBinary)
    totp_recovery: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    is_platform_admin: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
