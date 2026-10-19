"""Database and Redis fixtures. Tests that use them carry the db or redis marker."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from docu.db.base import Base
from docu.db.session import make_session_factory

pytestmark = [pytest.mark.db, pytest.mark.redis]


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("pgvector/pgvector:pg16") as postgres:
        url = postgres.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")
        yield url.replace("postgresql://", "postgresql+asyncpg://")


@pytest.fixture(scope="session")
def db_engine(postgres_url: str) -> Iterator[AsyncEngine]:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_url)
    command.upgrade(config, "head")
    engine = create_async_engine(postgres_url)
    yield engine


@pytest.fixture
async def db(db_engine: AsyncEngine):
    factory = make_session_factory(db_engine)
    yield factory
    async with db_engine.begin() as connection:
        names = ", ".join(table.name for table in reversed(Base.metadata.sorted_tables))
        await connection.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))


@pytest.fixture(scope="session")
def redis_url() -> Iterator[str]:
    from testcontainers.redis import RedisContainer

    with RedisContainer("redis:7-alpine") as redis:
        host = redis.get_container_host_ip()
        port = redis.get_exposed_port(6379)
        yield f"redis://{host}:{port}/0"


@pytest.fixture
async def redis(redis_url: str):
    from redis.asyncio import Redis

    client: Redis[bytes] = Redis.from_url(redis_url)
    yield client
    await client.flushdb()
    await client.aclose()
