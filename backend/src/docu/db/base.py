"""SQLAlchemy base, keys, and the shared column mixins."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from docu.domain.ids import new_uuid

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)


class UUIDPk:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=new_uuid)


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SoftDelete:
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TenantMixin:
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )


__all__ = ["Base", "SoftDelete", "TenantMixin", "Timestamps", "UUIDPk"]
