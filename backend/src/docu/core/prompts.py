"""Load Markdown prompt templates from the prompts/ directory.

Edit files under `prompts/` (or `PROMPT_DIR`) and restart the API.
Templates use `str.format_map` placeholders. A missing `{name}` stays literal.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any

__all__ = ["clear_prompt_cache", "load_prompt", "set_prompt_override_resolver"]

_resolver: Callable[[str], str | None] | None = None


class _SafeMap(dict[str, Any]):
    """Leave unknown `{placeholders}` intact so tool-name backticks stay valid."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def set_prompt_override_resolver(fn: Callable[[str], str | None] | None) -> None:
    """Install a DB override lookup. ``None`` clears it. T218 supplies the real one."""
    global _resolver
    _resolver = fn


def _resolve_dir(prompt_dir: Path | str | None) -> Path:
    if prompt_dir is None:
        from docu.core.config import get_settings

        return Path(get_settings().prompts.dir)
    return Path(prompt_dir)


@lru_cache(maxsize=64)
def _read_file(path: str) -> str:
    text = Path(path).read_text(encoding="utf-8")
    return text.strip() + "\n"


def load_prompt(
    name: str,
    *,
    prompt_dir: Path | str | None = None,
    **values: Any,
) -> str:
    """Return `prompts/{name}.md`, optionally formatted with `values`.

    `name` is the stem only (e.g. ``"date_context"`` → ``date_context.md``).
    A resolver, when set, wins over the file.
    """
    stem = name.removesuffix(".md")
    override = _resolver(stem) if _resolver is not None else None
    if override is None:
        path = _resolve_dir(prompt_dir) / f"{stem}.md"
        if not path.is_file():
            raise FileNotFoundError(f"prompt file not found: {path}")
        body = _read_file(str(path.resolve()))
    else:
        body = override.strip() + "\n"
    if not values:
        return body.rstrip("\n")
    return body.format_map(_SafeMap(values)).rstrip("\n")


def clear_prompt_cache() -> None:
    """Drop cached file contents (useful in tests after rewriting a prompt)."""
    _read_file.cache_clear()
