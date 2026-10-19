"""Web search / page-fetch settings face."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["WEB_FLAT", "WebSettings"]


class WebSettings(BaseModel):
    """Defaults for web_search and fetch_url."""

    search_results: int = Field(default=8, gt=0, le=10)
    fetch_timeout: float = Field(default=30.0, gt=0)
    max_page_chars: int = Field(default=8_000, gt=0)


WEB_FLAT: dict[str, str] = {
    "search_results": "search_results",
    "fetch_timeout": "fetch_timeout",
    "max_page_chars": "max_page_chars",
}
