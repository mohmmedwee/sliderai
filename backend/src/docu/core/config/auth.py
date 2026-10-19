"""Auth / session settings face."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

__all__ = ["AUTH_FLAT", "AuthSettings"]


class AuthSettings(BaseModel):
    """Session cookies, first-user bootstrap, and public origins."""

    secret_key: str = Field(min_length=32)
    session_ttl_days: int = Field(default=30, gt=0)
    cookie_secure: bool = Field(default=True)
    first_user_is_admin: bool = Field(default=False)
    google_client_id: str = Field(default="")
    google_client_secret: str = Field(default="")
    public_base_url: str = Field(default="http://127.0.0.1:8000")
    frontend_origin: str = Field(default="http://localhost:5173")

    @field_validator("public_base_url", "frontend_origin")
    @classmethod
    def _strip_url(cls, value: str) -> str:
        return value.strip().rstrip("/")

    @property
    def session_ttl(self) -> int:
        """Cookie lifetime in seconds. Ports that read ``session_ttl`` keep working."""
        return self.session_ttl_days * 24 * 60 * 60


AUTH_FLAT: dict[str, str] = {
    "secret_key": "secret_key",
    "session_ttl_days": "session_ttl_days",
    "cookie_secure": "cookie_secure",
    "first_user_is_admin": "first_user_is_admin",
    "google_client_id": "google_client_id",
    "google_client_secret": "google_client_secret",
    "public_base_url": "public_base_url",
    "frontend_origin": "frontend_origin",
}
