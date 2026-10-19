"""Billing settings face. Plan amounts are placeholders until FR-034 is decided."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["BILLING_FLAT", "BillingSettings"]


class BillingSettings(BaseModel):
    """Stripe test-mode keys and placeholder plan prices."""

    stripe_secret_key: str = Field(default="")
    stripe_webhook_secret: str = Field(default="")
    credit_margin: float = Field(default=1.3, gt=0)
    # FR-034 placeholders. See BLOCKED.md.
    plan_price_cents: dict[str, int] = Field(
        default_factory=lambda: {"free": 0, "plus": 1_900, "pro": 4_900, "team": 15_000}
    )
    plan_monthly_credits: dict[str, int] = Field(
        default_factory=lambda: {"free": 200, "plus": 2_000, "pro": 8_000, "team": 40_000}
    )


BILLING_FLAT: dict[str, str] = {
    "stripe_secret_key": "stripe_secret_key",
    "stripe_webhook_secret": "stripe_webhook_secret",
    "credit_margin": "credit_margin",
}
