from __future__ import annotations

try:
    import stripe as _stripe_sdk
except ModuleNotFoundError:  # pragma: no cover - local fallback when stripe is absent
    _stripe_sdk = None


def _stripe():
    if _stripe_sdk is None:
        import stripe

        return stripe
    return _stripe_sdk


if _stripe_sdk is not None:
    StripeError = _stripe_sdk.StripeError
    SignatureVerificationError = _stripe_sdk.SignatureVerificationError
else:
    class StripeError(Exception):
        pass


    class SignatureVerificationError(StripeError):
        pass


def create_checkout_session(*, api_key: str, **kwargs):
    stripe = _stripe()
    stripe.api_key = api_key
    return stripe.checkout.Session.create(**kwargs)


def construct_webhook_event(*, payload: bytes, sig_header: str, secret: str) -> dict:
    stripe = _stripe()
    return stripe.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=secret)
