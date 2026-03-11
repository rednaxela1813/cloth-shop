from __future__ import annotations

from decimal import Decimal

from .models import Order

_FREE_SHIPPING_THRESHOLD = Decimal("120.00")


def normalize_shipping_method(raw_value: str | None) -> str:
    value = (raw_value or "").strip()
    available = {choice for choice, _ in Order.ShippingMethod.choices}
    if value in available:
        return value
    return Order.ShippingMethod.DPD_HOME


def calculate_shipping_cost(*, shipping_method: str, subtotal: Decimal, country: str | None = None) -> Decimal:
    method = normalize_shipping_method(shipping_method)
    country_code = (country or "").strip().upper()

    if method == Order.ShippingMethod.PAKETA_PICKUP:
        base = Decimal("2.90")
    elif method == Order.ShippingMethod.DPD_EXPRESS:
        base = Decimal("7.90")
    else:
        base = Decimal("4.90")

    # Free shipping applies to standard delivery methods above threshold.
    if method in {Order.ShippingMethod.PAKETA_PICKUP, Order.ShippingMethod.DPD_HOME} and subtotal >= _FREE_SHIPPING_THRESHOLD:
        base = Decimal("0.00")

    # Non-SK/CZ delivery is usually pricier for last-mile.
    if country_code and country_code not in {"SK", "CZ"}:
        base += Decimal("2.00")

    return base.quantize(Decimal("0.01"))
