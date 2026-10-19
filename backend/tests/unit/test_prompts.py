"""Prompt templates load from a directory and optional DB override."""

from __future__ import annotations

from pathlib import Path

import pytest

from docu.core.prompts import clear_prompt_cache, load_prompt, set_prompt_override_resolver


@pytest.fixture(autouse=True)
def _clear_cache() -> object:
    clear_prompt_cache()
    set_prompt_override_resolver(None)
    yield
    clear_prompt_cache()
    set_prompt_override_resolver(None)


def test_date_context_substitutes(tmp_path: Path) -> None:
    (tmp_path / "date_context.md").write_text("Today is {today}.\n", encoding="utf-8")
    assert load_prompt("date_context", prompt_dir=tmp_path, today="Monday") == "Today is Monday."


def test_missing_variable_stays_literal(tmp_path: Path) -> None:
    (tmp_path / "date_context.md").write_text("Hello {name}.\n", encoding="utf-8")
    assert load_prompt("date_context", prompt_dir=tmp_path) == "Hello {name}."


def test_missing_prompt_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_prompt("nope", prompt_dir=tmp_path)


def test_override_resolver_wins(tmp_path: Path) -> None:
    (tmp_path / "date_context.md").write_text("from-file {today}\n", encoding="utf-8")
    set_prompt_override_resolver(lambda name: "from-db" if name == "date_context" else None)
    assert load_prompt("date_context", prompt_dir=tmp_path, today="Monday") == "from-db"
