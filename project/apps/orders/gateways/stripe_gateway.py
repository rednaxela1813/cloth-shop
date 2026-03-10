from __future__ import annotations

import stripe

# Re-export SDK exception classes from one place.
StripeError = stripe.StripeError
SignatureVerificationError = stripe.SignatureVerificationError


def create_checkout_session(*, api_key: str, **kwargs):
    stripe.api_key = api_key
    return stripe.checkout.Session.create(**kwargs)


def construct_webhook_event(*, payload: bytes, sig_header: str, secret: str) -> dict:
    return stripe.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=secret)
