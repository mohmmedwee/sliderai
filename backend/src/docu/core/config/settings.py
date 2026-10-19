"""Root application settings — env + nested faces only."""

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from docu.core.config.agent import AGENT_FLAT, AgentSettings
from docu.core.config.auth import AUTH_FLAT, AuthSettings
from docu.core.config.billing import BILLING_FLAT, BillingSettings
from docu.core.config.celery import CELERY_FLAT, CelerySettings
from docu.core.config.database import DATABASE_FLAT, DatabaseSettings
from docu.core.config.fake import FAKE_FLAT, FakeSettings
from docu.core.config.files import FILES_FLAT, FilesSettings
from docu.core.config.hoist import hoist_group
from docu.core.config.llm import LLM_FLAT, LlmSettings
from docu.core.config.mail import MAIL_FLAT, MailSettings
from docu.core.config.mcp import MCP_FLAT, McpSettings
from docu.core.config.memory import MEMORY_FLAT, MemorySettings
from docu.core.config.observability import OBSERVABILITY_FLAT, ObservabilitySettings
from docu.core.config.product import PRODUCT_FLAT, ProductSettings
from docu.core.config.prompts import PROMPTS_FLAT, PromptsSettings
from docu.core.config.redis import REDIS_FLAT, RedisSettings
from docu.core.config.skills import SKILLS_FLAT, SkillsSettings
from docu.core.config.storage import STORAGE_FLAT, StorageSettings
from docu.core.config.web import WEB_FLAT, WebSettings

__all__ = ["Settings"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm: LlmSettings = Field(default_factory=LlmSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    files: FilesSettings = Field(default_factory=FilesSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    skills: SkillsSettings = Field(default_factory=SkillsSettings)
    mcp: McpSettings = Field(default_factory=McpSettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    auth: AuthSettings
    memory: MemorySettings = Field(default_factory=MemorySettings)
    web: WebSettings = Field(default_factory=WebSettings)
    prompts: PromptsSettings = Field(default_factory=PromptsSettings)
    mail: MailSettings = Field(default_factory=MailSettings)
    billing: BillingSettings = Field(default_factory=BillingSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    fake: FakeSettings = Field(default_factory=FakeSettings)
    product: ProductSettings = Field(default_factory=ProductSettings)

    @model_validator(mode="before")
    @classmethod
    def _hoist_flat_into_nested(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        out = dict(data)
        hoist_group(out, "llm", LLM_FLAT)
        hoist_group(out, "mcp", MCP_FLAT)
        hoist_group(out, "agent", AGENT_FLAT)
        hoist_group(out, "database", DATABASE_FLAT)
        hoist_group(out, "redis", REDIS_FLAT)
        hoist_group(out, "storage", STORAGE_FLAT)
        hoist_group(out, "files", FILES_FLAT)
        hoist_group(out, "skills", SKILLS_FLAT)
        hoist_group(out, "auth", AUTH_FLAT)
        hoist_group(out, "memory", MEMORY_FLAT)
        hoist_group(out, "web", WEB_FLAT)
        hoist_group(out, "prompts", PROMPTS_FLAT)
        hoist_group(out, "mail", MAIL_FLAT)
        hoist_group(out, "billing", BILLING_FLAT)
        hoist_group(out, "celery", CELERY_FLAT)
        hoist_group(out, "observability", OBSERVABILITY_FLAT)
        hoist_group(out, "fake", FAKE_FLAT)
        hoist_group(out, "product", PRODUCT_FLAT)
        return out

    @model_validator(mode="after")
    def _finish(self) -> Settings:
        self.agent.context_window = self.llm.context_window
        self.agent.max_completion_tokens = self.llm.max_completion_tokens
        self.files.file_storage = self.storage.file_storage
        self.files.upload_dir = self.storage.upload_dir
        self.files.s3_bucket = self.storage.s3_bucket
        self.files.s3_endpoint_url = self.storage.s3_endpoint_url or None
        self.files.s3_region = self.storage.s3_region
        self.files.s3_access_key = self.storage.s3_access_key
        self.files.s3_secret_key = self.storage.s3_secret_key
        self.files.max_upload_bytes = self.storage.max_upload_bytes
        if not self.celery.broker_url:
            self.celery.broker_url = self.redis.url
        if not self.fake.agent_fake_model and (not self.llm.upstream or not self.llm.model):
            raise ValueError("UPSTREAM and MODEL are required unless AGENT_FAKE_MODEL is set")
        return self
