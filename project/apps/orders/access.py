from __future__ import annotations

from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.utils.crypto import constant_time_compare


TOKEN_SALT = "orders.guest-access"


def _ensure_session_key(request) -> str:
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def issue_guest_order_access_token(request, order) -> str:
    """
    Issue a signed token for guest order access.
    The token is bound to order public_id + current session key.
    """
    session_key = _ensure_session_key(request)
    signer = TimestampSigner(salt=TOKEN_SALT)
    payload = f"{order.public_id}:{session_key}"
    return signer.sign(payload)


def validate_guest_order_access_token(request, order, token: str) -> bool:
    if not token:
        return False
    session_key = request.session.session_key
    if not session_key:
        return False

    signer = TimestampSigner(salt=TOKEN_SALT)
    max_age = getattr(settings, "ORDER_ACCESS_TOKEN_MAX_AGE", 2 * 60 * 60)
    try:
        payload = signer.unsign(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return False

    expected = f"{order.public_id}:{session_key}"
    return constant_time_compare(payload, expected)
