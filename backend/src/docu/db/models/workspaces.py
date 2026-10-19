"""Workspaces, memberships, and invitations."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column

from docu.db.base import Base, TenantMixin, Timestamps, UUIDPk

__all__ = ["Invitation", "Membership", "Workspace"]


class Workspace(UUIDPk, Timestamps, Base):
    __tablename__ = "workspaces"
    __table_args__ = (
        CheckConstraint("kind in ('personal', 'team')", name="kind"),
        CheckConstraint("plan in ('free', 'pro', 'team')", name="plan"),
    )

    name: Mapped[str] = mapped_column(Text)
    slug: Mapped[str] = mapped_column(Text, unique=True)
    kind: Mapped[str] = mapped_column(Text)
    plan: Mapped[str] = mapped_column(Text)
    stripe_customer_id: Mapped[str | None] = mapped_column(Text)
    credit_balance: Mapped[int] = mapped_column(default=0)
    data_region: Mapped[str] = mapped_column(Text)


class Membership(UUIDPk, Timestamps, TenantMixin, Base):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id"),
        CheckConstraint("role in ('owner', 'admin', 'editor', 'viewer')", name="role"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(Text)


class Invitation(UUIDPk, Timestamps, TenantMixin, Base):
    __tablename__ = "invitations"
    __table_args__ = (
        CheckConstraint(
            "role in ('owner', 'admin', 'editor', 'viewer', 'view', 'edit')",
            name="role",
        ),
        CheckConstraint("status in ('pending', 'accepted', 'revoked', 'expired')", name="status"),
    )

    document_id: Mapped[UUID | None] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    email: Mapped[str] = mapped_column(CITEXT)
    role: Mapped[str] = mapped_column(Text)
    token_hash: Mapped[str] = mapped_column(Text)
    invited_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(Text)
