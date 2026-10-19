"""MCP settings face — what the MCP package depends on."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

__all__ = ["MCP_FLAT", "McpSettings"]


class McpSettings(BaseModel):
    """Small settings face for the MCP package."""

    enabled: bool = Field(default=True)
    config_path: Path = Field(default=Path("mcp.json"))
    require_approval: bool = Field(default=False)
    max_servers_per_user: int = Field(default=20, gt=0)
    connect_timeout_sec: float = Field(default=45.0, gt=0)
    max_instructions_chars: int = Field(default=8_000, gt=0)
    max_upload_bytes: int = Field(default=25 * 1024 * 1024, gt=0)
    oauth_client_id: str | None = Field(default=None)
    oauth_client_secret: str | None = Field(default=None)


MCP_FLAT: dict[str, str] = {
    "mcp_enabled": "enabled",
    "mcp_config_path": "config_path",
    "mcp_require_approval": "require_approval",
    "max_mcp_servers_per_user": "max_servers_per_user",
    "mcp_connect_timeout_sec": "connect_timeout_sec",
    "mcp_max_instructions_chars": "max_instructions_chars",
    "mcp_max_upload_bytes": "max_upload_bytes",
    "mcp_oauth_client_id": "oauth_client_id",
    "mcp_oauth_client_secret": "oauth_client_secret",
}
