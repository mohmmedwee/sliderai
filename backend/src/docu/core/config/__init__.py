"""Application settings package — nested faces + process-wide cache."""

from __future__ import annotations

from docu.core.config.agent import AgentSettings
from docu.core.config.auth import AuthSettings
from docu.core.config.billing import BillingSettings
from docu.core.config.cache import (
    clear_settings,
    get_settings,
    override_settings,
    settings_override,
)
from docu.core.config.celery import CelerySettings
from docu.core.config.database import DatabaseSettings
from docu.core.config.fake import FakeSettings
from docu.core.config.files import FilesSettings
from docu.core.config.llm import LlmSettings
from docu.core.config.mail import MailSettings
from docu.core.config.mcp import McpSettings
from docu.core.config.memory import MemorySettings
from docu.core.config.observability import ObservabilitySettings
from docu.core.config.product import ProductSettings
from docu.core.config.prompts import PromptsSettings
from docu.core.config.redis import RedisSettings
from docu.core.config.settings import Settings
from docu.core.config.skills import SkillsSettings
from docu.core.config.storage import StorageSettings
from docu.core.config.web import WebSettings

__all__ = [
    "AgentSettings",
    "AuthSettings",
    "BillingSettings",
    "CelerySettings",
    "DatabaseSettings",
    "FakeSettings",
    "FilesSettings",
    "LlmSettings",
    "MailSettings",
    "McpSettings",
    "MemorySettings",
    "ObservabilitySettings",
    "ProductSettings",
    "PromptsSettings",
    "RedisSettings",
    "Settings",
    "SkillsSettings",
    "StorageSettings",
    "WebSettings",
    "clear_settings",
    "get_settings",
    "override_settings",
    "settings_override",
]
