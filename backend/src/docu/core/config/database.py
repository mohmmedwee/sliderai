"""Postgres settings face."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["DATABASE_FLAT", "DatabaseSettings"]


class DatabaseSettings(BaseModel):
    """SQLAlchemy / Postgres connection settings."""

    url: str = Field(
        default="postgresql+asyncpg://docu:docu@localhost:5432/docu",
    )
    echo: bool = Field(default=False)


DATABASE_FLAT: dict[str, str] = {
    "database_url": "url",
    "database_echo": "echo",
}
