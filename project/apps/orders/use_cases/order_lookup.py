from __future__ import annotations

from dataclasses import dataclass

from django.shortcuts import get_object_or_404

from apps.orders.models import Order
from apps.orders.use_cases.authorize_order_access import ensure_order_access


@dataclass(frozen=True)
class AccessibleOrder:
    order: Order
    access_token: str


def get_accessible_order(request, public_id) -> AccessibleOrder:
    """
    Load order by public id and enforce access in one place.
    This avoids duplicating lookup+authorization logic in multiple views.
    """
    order = get_object_or_404(Order, public_id=public_id)
    access_token = ensure_order_access(request, order)
    return AccessibleOrder(order=order, access_token=access_token)
