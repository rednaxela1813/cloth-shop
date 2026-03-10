from __future__ import annotations

import logging
from dataclasses import dataclass

from apps.orders.gateways import stripe_gateway
from apps.orders.services import handle_stripe_webhook_event

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebhookResult:
    ok: bool
    error_message: str = ""


def process_stripe_webhook(*, payload: bytes, signature: str, webhook_secret: str) -> WebhookResult:
    if not webhook_secret:
        logger.error(
            "Stripe webhook secret is not configured",
            extra={"event_type": "webhook.config_error", "stripe_session_id": ""},
        )
        return WebhookResult(ok=False, error_message="Missing STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe_gateway.construct_webhook_event(
            payload=payload,
            sig_header=signature,
            secret=webhook_secret,
        )
    except (ValueError, stripe_gateway.SignatureVerificationError):
        logger.warning(
            "Stripe webhook signature validation failed",
            extra={"event_type": "webhook.invalid_signature", "stripe_session_id": ""},
        )
        return WebhookResult(ok=False, error_message="Invalid webhook signature")

    handle_stripe_webhook_event(event)
    return WebhookResult(ok=True)
