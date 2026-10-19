"""Document queries. Later repositories follow this shape."""

from __future__ import annotations

import base64
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from docu.db.models import Document
from docu.db.repositories import Page

__all__ = ["get", "list_recent"]


async def get(session: AsyncSession, *, workspace_id: UUID, doc_id: UUID) -> Document | None:
    result = await session.execute(
        select(Document).where(
            Document.workspace_id == workspace_id,
            Document.id == doc_id,
            Document.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_recent(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    limit: int,
    cursor: str | None,
) -> Page[Document]:
    stmt = select(Document).where(
        Document.workspace_id == workspace_id,
        Document.deleted_at.is_(None),
    )
    if cursor:
        stamp, doc_id = _decode_cursor(cursor)
        stmt = stmt.where(tuple_(Document.updated_at, Document.id) < tuple_(stamp, doc_id))
    stmt = stmt.order_by(Document.updated_at.desc(), Document.id.desc()).limit(limit + 1)
    rows = list((await session.execute(stmt)).scalars())
    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = _encode_cursor(last.updated_at, last.id)
        rows = rows[:limit]
    return Page(items=rows, next_cursor=next_cursor)


def _encode_cursor(updated_at: datetime, doc_id: UUID) -> str:
    raw = f"{updated_at.isoformat()}|{doc_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    stamp, doc_id = raw.split("|", 1)
    return datetime.fromisoformat(stamp), UUID(doc_id)
