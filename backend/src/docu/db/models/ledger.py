"""Append-only credit ledger. Rows are never updated or deleted."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from docu.db.base import Base, UUIDPk

__all__ = ["CreditLedger"]


class CreditLedger(UUIDPk, Base):
    __tablename__ = "credit_ledger"
    __table_args__ = (
        CheckConstraint(
            "kind in ('grant', 'reserve', 'settle', 'refund', 'image', 'adjust')",
            name="kind",
        ),
        Index("ix_credit_ledger_workspace_created", "workspace_id", "created_at"),
    )

    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"))
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    delta: Mapped[int]
    kind: Mapped[str] = mapped_column(Text)
    turn_id: Mapped[UUID | None] = mapped_column()
    asset_id: Mapped[UUID | None] = mapped_column()
    stripe_invoice_id: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
