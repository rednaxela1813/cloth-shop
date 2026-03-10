from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CheckoutSuccessPageContext:
    # Explicit page DTO keeps templates decoupled from view internals.
    order: object


@dataclass(frozen=True)
class PaymentReturnPageContext:
    # Normalize status handling in one place for all callers.
    status: str


def build_checkout_success_context(order_ctx) -> CheckoutSuccessPageContext:
    return CheckoutSuccessPageContext(order=order_ctx.order)


def build_payment_return_context(raw_status: str | None) -> PaymentReturnPageContext:
    return PaymentReturnPageContext(status=raw_status or "unknown")
