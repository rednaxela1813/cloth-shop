from __future__ import annotations

from apps.cart.models import Cart
from apps.orders.models import Order


def build_account_dashboard_context(*, user) -> dict:
    active_cart = (
        Cart.objects.filter(user=user, is_active=True)
        .prefetch_related("items", "items__variant", "items__variant__images", "items__variant__product", "items__variant__product__images")
        .first()
    )
    recent_orders = list(
        user.orders.select_related("shipping_address")
        .prefetch_related("items", "items__variant", "items__variant__images", "items__variant__product", "items__variant__product__images")
        .order_by("-created", "-id")[:5]
    )
    cart_items_count = sum(item.quantity for item in active_cart.items.all()) if active_cart else 0
    cart_subtotal = active_cart.subtotal if active_cart else 0
    return {
        "recent_orders": recent_orders,
        "active_cart_items": list(active_cart.items.all()) if active_cart else [],
        "orders_count": user.orders.count(),
        "pending_orders_count": user.orders.filter(status=Order.Status.PENDING).count(),
        "cart_items_count": cart_items_count,
        "cart_subtotal": cart_subtotal,
    }


def build_account_orders_context(*, user) -> dict:
    orders = (
        user.orders.select_related("shipping_address")
        .prefetch_related("items", "items__variant", "items__variant__images", "items__variant__product", "items__variant__product__images")
        .order_by("-created", "-id")
    )
    return {
        "orders": orders,
    }
