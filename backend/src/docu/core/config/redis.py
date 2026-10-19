"""Redis + response-cache settings face."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["REDIS_FLAT", "RedisSettings"]


class RedisSettings(BaseModel):
    """Redis connection and cache TTLs (search / fetch)."""

    url: str = Field(default="redis://localhost:6379/0")
    prefix: str = Field(default="docu:")
    cache_search_ttl: int = Field(default=3600, gt=0)
    cache_fetch_ttl: int = Field(default=86_400, gt=0)


REDIS_FLAT: dict[str, str] = {
    "redis_url": "url",
    "redis_prefix": "prefix",
    "cache_search_ttl": "cache_search_ttl",
    "cache_fetch_ttl": "cache_fetch_ttl",
}
