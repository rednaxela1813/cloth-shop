from __future__ import annotations

from urllib.parse import urlencode

from django.http import Http404
from django.urls import reverse

from apps.orders.access import issue_guest_order_access_token, validate_guest_order_access_token


def ensure_order_access(request, order) -> str:
    """
    Returns guest access token when needed, raises 404 if access is denied.
    """
    if order.user_id:
        if not request.user.is_authenticated or request.user.id != order.user_id:
            raise Http404("Order not found")
        return ""

    token = request.GET.get("access_token", "")
    if not validate_guest_order_access_token(request, order, token):
        raise Http404("Order not found")
    return token


def build_guest_payment_start_redirect(request, order) -> str:
    token = issue_guest_order_access_token(request, order)
    return (
        reverse("orders:payment_start", kwargs={"public_id": order.public_id})
        + "?"
        + urlencode({"access_token": token})
    )
