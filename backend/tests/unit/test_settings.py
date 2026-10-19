"""Settings load from env names and can be overridden in tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from docu.core.config import (
    Settings,
    clear_settings,
    get_settings,
    override_settings,
    settings_override,
)

SECRET = "test-secret-key-32-bytes-minimum!!"


@pytest.fixture(autouse=True)
def _reset_settings() -> object:
    clear_settings()
    yield
    clear_settings()


def test_upstream_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", SECRET)
    monkeypatch.setenv("AGENT_FAKE_MODEL", "1")
    monkeypatch.setenv("UPSTREAM", "http://x/v1")
    monkeypatch.setenv("CONTEXT_WINDOW", "32768")
    clear_settings()
    settings = get_settings()
    assert settings.llm.upstream == "http://x/v1"
    assert settings.llm.context_window == 32768
    assert settings.agent.context_window == 32768
    assert settings.skills.max_chars == 24_000
    assert settings.prompts.dir.name == "prompts"


def test_missing_secret_key_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    clear_settings()
    with pytest.raises(ValidationError):
        get_settings()


def test_override_settings() -> None:
    custom = Settings(
        auth={"secret_key": SECRET},
        fake={"agent_fake_model": True},
        llm={"model": "test-model-xyz", "upstream": "http://x/v1"},
    )
    override_settings(custom)
    assert get_settings() is custom
    assert get_settings().llm.model == "test-model-xyz"

    other = Settings(
        auth={"secret_key": SECRET},
        fake={"agent_fake_model": True},
        llm={"model": "temp-model", "upstream": "http://x/v1"},
    )
    with settings_override(other):
        assert get_settings() is other
    assert get_settings() is custom


def test_fake_model_makes_upstream_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", SECRET)
    monkeypatch.setenv("AGENT_FAKE_MODEL", "1")
    monkeypatch.delenv("UPSTREAM", raising=False)
    monkeypatch.delenv("MODEL", raising=False)
    clear_settings()
    settings = get_settings()
    assert settings.llm.upstream == ""
    assert settings.llm.model == ""


def test_upstream_required_without_fake(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", SECRET)
    monkeypatch.setenv("AGENT_FAKE_MODEL", "0")
    monkeypatch.delenv("UPSTREAM", raising=False)
    monkeypatch.delenv("MODEL", raising=False)
    clear_settings()
    with pytest.raises(ValidationError):
        get_settings()
