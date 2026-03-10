from dataclasses import dataclass

from apps.orders.use_cases.present_order_pages import (
    build_checkout_success_context,
    build_payment_return_context,
)


@dataclass
class _DummyOrderContext:
    order: object


def test_build_checkout_success_context_returns_order():
    order_obj = object()
    ctx = build_checkout_success_context(_DummyOrderContext(order=order_obj))
    assert ctx.order is order_obj


def test_build_payment_return_context_defaults_unknown():
    ctx = build_payment_return_context(None)
    assert ctx.status == "unknown"


def test_build_payment_return_context_keeps_explicit_status():
    ctx = build_payment_return_context("success")
    assert ctx.status == "success"
