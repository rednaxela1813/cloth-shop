from __future__ import annotations

from decimal import Decimal

from apps.orders.models import Order
from .models import ReturnPolicyConfig, ShippingProviderConfig

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

    if method in {Order.ShippingMethod.PAKETA_PICKUP, Order.ShippingMethod.DPD_HOME} and subtotal >= _FREE_SHIPPING_THRESHOLD:
        base = Decimal("0.00")

    if country_code and country_code not in {"SK", "CZ"}:
        base += Decimal("2.00")

    return base.quantize(Decimal("0.01"))


def get_delivery_eta_label(default: str = "24–48 h") -> str:
    config = ShippingProviderConfig.objects.filter(is_active=True).order_by("provider").first()
    if config and config.delivery_eta_label.strip():
        return config.delivery_eta_label.strip()
    return default


def get_return_policy_config():
    return ReturnPolicyConfig.objects.filter(is_active=True).order_by("id").first()


def get_return_window_days(default: int = 30) -> int:
    config = get_return_policy_config()
    if config:
        return config.return_window_days
    return default


def get_return_window_label(default: str = "30 dní bez rizika") -> str:
    days = get_return_window_days(default=30)
    if days == 1:
        return "1 deň na vrátenie"
    return f"{days} dní bez rizika"
