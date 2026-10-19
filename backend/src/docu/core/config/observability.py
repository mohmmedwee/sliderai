"""Tracing and error-reporting settings face."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["OBSERVABILITY_FLAT", "ObservabilitySettings"]


class ObservabilitySettings(BaseModel):
    """Sentry, OpenTelemetry, and LangSmith."""

    sentry_dsn: str = Field(default="")
    otel_exporter_otlp_endpoint: str = Field(default="")
    langsmith_tracing: bool = Field(default=False)
    langsmith_api_key: str = Field(default="")
    langsmith_project: str = Field(default="docu")


OBSERVABILITY_FLAT: dict[str, str] = {
    "sentry_dsn": "sentry_dsn",
    "otel_exporter_otlp_endpoint": "otel_exporter_otlp_endpoint",
    "langsmith_tracing": "langsmith_tracing",
    "langsmith_api_key": "langsmith_api_key",
    "langsmith_project": "langsmith_project",
}
