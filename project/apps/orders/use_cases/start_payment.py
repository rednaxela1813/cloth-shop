from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import urlencode

from django.urls import reverse

from apps.orders.gateways import stripe_gateway
from apps.orders.models import Payment
from apps.orders.services import cancel_order_and_restore_stock_if_pending, create_stripe_payment

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StartPaymentResult:
    payment: Payment | None
    error_status: str | None


@dataclass(frozen=True)
class StartPaymentHttpDecision:
    redirect_url: str | None = None
    bad_request_message: str | None = None


def get_or_create_stripe_payment(request, order) -> StartPaymentResult:
    payment = order.payments.filter(provider=Payment.Provider.STRIPE).order_by("-created").first()
    if payment:
        logger.info(
            "Payment start requested with existing Stripe payment",
            extra={
                "order_public_id": str(order.public_id),
                "payment_id": payment.id,
                "stripe_session_id": payment.external_id,
            },
        )
        return StartPaymentResult(payment=payment, error_status=None)

    logger.info(
        "Payment start requested, creating Stripe payment",
        extra={"order_public_id": str(order.public_id)},
    )
    try:
        payment = create_stripe_payment(request, order)
        return StartPaymentResult(payment=payment, error_status=None)
    except ValueError:
        cancel_order_and_restore_stock_if_pending(order, source="payment.start.error_config")
        logger.warning(
            "Stripe payment configuration error for order %s",
            order.public_id,
            extra={"order_public_id": str(order.public_id)},
        )
        return StartPaymentResult(payment=None, error_status="error_config")
    except stripe_gateway.StripeError as exc:
        cancel_order_and_restore_stock_if_pending(order, source="payment.start.error_gateway")
        logger.warning(
            "Stripe API error while creating payment for order %s: %s",
            order.public_id,
            str(exc),
            extra={"order_public_id": str(order.public_id)},
        )
        return StartPaymentResult(payment=None, error_status="error_gateway")
    except Exception:
        cancel_order_and_restore_stock_if_pending(order, source="payment.start.error")
        logger.exception(
            "Unexpected error while creating payment for order %s",
            order.public_id,
            extra={"order_public_id": str(order.public_id)},
        )
        return StartPaymentResult(payment=None, error_status="error")


def resolve_payment_start_decision(request, order, access_token: str) -> StartPaymentHttpDecision:
    # Order is already paid: redirect to success page and preserve guest token.
    if order.status == order.Status.PAID:
        success_url = reverse("orders:success", kwargs={"public_id": order.public_id})
        if access_token:
            success_url += "?" + urlencode({"access_token": access_token})
        return StartPaymentHttpDecision(redirect_url=success_url)

    result = get_or_create_stripe_payment(request, order)
    if result.error_status:
        return StartPaymentHttpDecision(
            redirect_url=reverse("orders:payment_return") + f"?status={result.error_status}"
        )

    payment = result.payment
    # Missing gateway URL is an application/data error, not a redirect case.
    if not payment or not payment.gateway_url:
        return StartPaymentHttpDecision(bad_request_message="Payment URL is missing")

    return StartPaymentHttpDecision(redirect_url=payment.gateway_url)
