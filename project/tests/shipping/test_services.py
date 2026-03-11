from decimal import Decimal

from apps.orders.models import Order
from apps.shipping.services import calculate_shipping_cost, normalize_shipping_method


def test_normalize_shipping_method_defaults_to_dpd_home():
    assert normalize_shipping_method("unknown") == Order.ShippingMethod.DPD_HOME


def test_calculate_shipping_cost_for_paketa_pickup():
    cost = calculate_shipping_cost(
        shipping_method=Order.ShippingMethod.PAKETA_PICKUP,
        subtotal=Decimal("50.00"),
        country="SK",
    )
    assert cost == Decimal("2.90")


def test_calculate_shipping_cost_for_dpd_home_free_shipping_threshold():
    cost = calculate_shipping_cost(
        shipping_method=Order.ShippingMethod.DPD_HOME,
        subtotal=Decimal("120.00"),
        country="SK",
    )
    assert cost == Decimal("0.00")


def test_calculate_shipping_cost_for_dpd_express_non_local_country():
    cost = calculate_shipping_cost(
        shipping_method=Order.ShippingMethod.DPD_EXPRESS,
        subtotal=Decimal("80.00"),
        country="DE",
    )
    assert cost == Decimal("9.90")
