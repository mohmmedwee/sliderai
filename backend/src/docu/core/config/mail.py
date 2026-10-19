"""Outbound mail settings face."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

__all__ = ["MAIL_FLAT", "MailSettings"]


class MailSettings(BaseModel):
    """SMTP (Mailpit in dev) or SES."""

    mail_backend: Literal["smtp", "ses"] = "smtp"
    smtp_host: str = Field(default="localhost")
    smtp_port: int = Field(default=1025, gt=0)
    mail_from: str = Field(default="docu@localhost")


MAIL_FLAT: dict[str, str] = {
    "mail_backend": "mail_backend",
    "smtp_host": "smtp_host",
    "smtp_port": "smtp_port",
    "mail_from": "mail_from",
}
