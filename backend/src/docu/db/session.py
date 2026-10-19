"""Request and worker sessions, including the one that bypasses row-level security."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

__all__ = ["make_session_factory", "scoped_session", "system_session", "unscoped_session"]


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def scoped_session(
    factory: async_sessionmaker[AsyncSession], workspace_id: UUID
) -> AsyncIterator[AsyncSession]:
    """Transaction whose RLS scope is one workspace. Commits on success."""
    async with factory() as session, session.begin():
        await session.execute(
            text("SELECT set_config('app.workspace_id', :w, true)"),
            {"w": str(workspace_id)},
        )
        yield session


@asynccontextmanager
async def unscoped_session(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """For non-tenant tables only. RLS tables return no rows here."""
    async with factory() as session, session.begin():
        yield session


@asynccontextmanager
async def system_session(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Bypasses RLS for worker jobs that must see every workspace.

    Never import this from the API package.
    """
    async with factory() as session, session.begin():
        await session.execute(text("SELECT set_config('app.bypass_rls', 'on', true)"))
        yield session
