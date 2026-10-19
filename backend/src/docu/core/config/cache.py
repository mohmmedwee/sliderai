"""Process-wide settings cache — load once, reuse for the process lifetime.

Same idea as Django's ``django.conf.settings`` or FastAPI's recommended
``lru_cache`` on ``get_settings``: env is read once, every caller shares one
immutable-ish instance. Tests clear or override after changing the environment.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from docu.core.config.settings import Settings

__all__ = [
    "clear_settings",
    "get_settings",
    "override_settings",
    "settings_override",
]

_cached: Settings | None = None


def get_settings() -> Settings:
    """Return the cached Settings, building it from env on first call."""
    global _cached
    if _cached is None:
        _cached = Settings()
    return _cached


def clear_settings() -> None:
    """Drop the cache so the next ``get_settings()`` reloads from the environment."""
    global _cached
    _cached = None


def override_settings(settings: Settings) -> Settings:
    """Install ``settings`` as the process singleton (e.g. app startup / tests)."""
    global _cached
    _cached = settings
    return settings


@contextmanager
def settings_override(settings: Settings) -> Iterator[Settings]:
    """Temporarily replace cached settings; restore the previous value on exit."""
    global _cached
    previous = _cached
    _cached = settings
    try:
        yield settings
    finally:
        _cached = previous
