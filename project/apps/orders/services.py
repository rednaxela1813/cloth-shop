# apps/orders/services.py
from __future__ import annotations

import logging
from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError
from django.db import transaction
from django.urls import reverse

from apps.cart.models import Cart
from apps.products.models import ProductVariant
from apps.shipping.services import calculate_shipping_cost, normalize_shipping_method
from .gateways import stripe_gateway
from .models import Address, Order, OrderItem, Payment, ProcessedStripeEvent

logger = logging.getLogger(__name__)


def create_order_from_cart(request, cart: Cart, data: dict) -> Order:
    if not cart.items.exists():
        raise ValueError("Cannot create order from empty cart")

    with transaction.atomic():
        cart_items = list(cart.items.select_related("variant", "variant__product").order_by("id"))
        variant_ids = [item.variant_id for item in cart_items]
        locked_variants = {
            variant.id: variant
            for variant in ProductVariant.objects.select_for_update().select_related("product").filter(id__in=variant_ids)
        }

        for item in cart_items:
            variant = locked_variants.get(item.variant_id)
            if not variant or not variant.is_active or not variant.product.is_active:
                raise ValueError("One or more variants are unavailable")
            if item.quantity > variant.stock:
                raise ValueError(f"Not enough stock for {variant.product.name} ({variant.color}/{variant.size})")

        # Keep address snapshot for the order, even if user changes it later.
        address = Address.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=data["full_name"],
            email=data["email"],
            phone=data.get("phone", ""),
            country=data["country"],
            region=data.get("region", ""),
            city=data["city"],
            postal_code=data.get("postal_code", ""),
            address_line1=data["address_line1"],
            address_line2=data.get("address_line2", ""),
        )

        subtotal = Decimal("0.00")
        for item in cart_items:
            variant = locked_variants[item.variant_id]
            subtotal += variant.price * item.quantity

        shipping_method = normalize_shipping_method(data.get("shipping_method"))
        shipping_cost = calculate_shipping_cost(
            shipping_method=shipping_method,
            subtotal=subtotal,
            country=data.get("country"),
        )
        total = subtotal + shipping_cost

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            email=data["email"],
            shipping_address=address,
            shipping_method=shipping_method,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total=total,
        )

        for item in cart_items:
            variant = locked_variants[item.variant_id]
            line_total = variant.price * item.quantity
            OrderItem.objects.create(
                order=order,
                variant=variant,
                quantity=item.quantity,
                product_name=variant.product.name,
                sku=variant.sku,
                size=variant.size,
                color=variant.color,
                unit_price=variant.price,
                line_total=line_total,
            )
            variant.stock -= item.quantity
            variant.save(update_fields=["stock", "updated"])

        # Clear cart items after successful order creation.
        cart.items.all().delete()

    return order


def cancel_order_and_restore_stock_if_pending(order: Order, *, source: str) -> bool:
    """
    Atomically cancel pending order and return reserved stock back to variants.
    Returns True only when cancellation/restock was applied.
    """
    with transaction.atomic():
        locked_order = Order.objects.select_for_update().filter(id=order.id).first()
        if not locked_order or locked_order.status != Order.Status.PENDING:
            return False

        order_items = list(locked_order.items.select_related("variant").order_by("id"))
        variant_ids = [item.variant_id for item in order_items]
        locked_variants = {
            variant.id: variant
            for variant in ProductVariant.objects.select_for_update().filter(id__in=variant_ids)
        }

        for item in order_items:
            variant = locked_variants.get(item.variant_id)
            if not variant:
                continue
            variant.stock += item.quantity
            variant.save(update_fields=["stock", "updated"])

        locked_order._status_event_source = source
        locked_order.status = Order.Status.CANCELED
        locked_order.save(update_fields=["status", "updated"])

    logger.info(
        "Order canceled and stock restored",
        extra={
            "order_public_id": str(order.public_id),
            "event_type": source,
            "stripe_session_id": "",
        },
    )
    return True


def _to_minor_units(amount: Decimal) -> int:
    return int((amount * Decimal("100")).quantize(Decimal("1")))


def _validate_stripe_config() -> None:
    if not settings.STRIPE_SECRET_KEY:
        raise ValueError("Stripe is not configured. Set STRIPE_SECRET_KEY.")


def _stripe_client():
    _validate_stripe_config()
    return settings.STRIPE_SECRET_KEY


def create_stripe_payment(request, order: Order) -> Payment:
    payment = Payment.objects.create(
        order=order,
        provider=Payment.Provider.STRIPE,
        status=Payment.Status.CREATED,
        amount=order.total,
        currency=order.currency,
    )
    stripe_api_key = _stripe_client()

    success_url = (
        request.build_absolute_uri(reverse("orders:payment_return"))
        + "?status=success&session_id={CHECKOUT_SESSION_ID}"
    )
    cancel_url = request.build_absolute_uri(reverse("orders:payment_return")) + "?status=cancel"
    session = stripe_gateway.create_checkout_session(
        api_key=stripe_api_key,
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=order.email,
        client_reference_id=str(order.public_id),
        metadata={"order_public_id": str(order.public_id)},
        line_items=[
            {
                "price_data": {
                    "currency": order.currency.lower(),
                    "unit_amount": _to_minor_units(order.total),
                    "product_data": {"name": f"Order {order.public_id}"},
                },
                "quantity": 1,
            }
        ],
        payment_intent_data={"metadata": {"order_public_id": str(order.public_id)}},
    )

    payment.external_id = session.id or ""
    payment.gateway_url = session.url or cancel_url
    payment.raw_response = session.to_dict_recursive()
    payment._status_event_source = "payment.start"
    payment.status = Payment.Status.PENDING
    payment.save(update_fields=["external_id", "gateway_url", "raw_response", "status", "updated"])
    logger.info(
        "Stripe checkout session created",
        extra={
            "order_public_id": str(order.public_id),
            "payment_id": payment.id,
            "stripe_session_id": payment.external_id,
            "event_type": "checkout.session.created",
        },
    )
    return payment


def _apply_payment_status(payment: Payment, new_status: str) -> None:
    old_status = payment.status
    payment._status_event_source = f"payment.status.{new_status}"
    payment.status = new_status
    payment.save(update_fields=["status", "updated"])

    logger.info(
        "Payment status changed",
        extra={
            "order_public_id": str(payment.order.public_id),
            "payment_id": payment.id,
            "stripe_session_id": payment.external_id,
            "event_type": "payment.status.change",
            "old_status": old_status,
            "new_status": new_status,
        },
    )

    if new_status == Payment.Status.PAID:
        if payment.order.status != Order.Status.PAID:
            payment.order._status_event_source = "payment.status.paid"
            payment.order.status = Order.Status.PAID
            payment.order.save(update_fields=["status", "updated"])
    elif new_status in {Payment.Status.CANCELED, Payment.Status.FAILED}:
        cancel_order_and_restore_stock_if_pending(
            payment.order,
            source=f"payment.status.{new_status}",
        )


def handle_stripe_webhook_event(event: dict) -> None:
    event_id = event.get("id", "")
    if not event_id:
        logger.warning(
            "Stripe webhook missing event id",
            extra={"event_type": "webhook.invalid", "stripe_session_id": ""},
        )
        return

    event_type = event.get("type", "")
    data_obj = (event.get("data") or {}).get("object") or {}
    session_id = data_obj.get("id")
    if not session_id:
        logger.warning(
            "Stripe webhook missing session id",
            extra={"event_type": event_type or "webhook.invalid", "stripe_session_id": ""},
        )
        return

    with transaction.atomic():
        try:
            ProcessedStripeEvent.objects.create(
                stripe_event_id=str(event_id),
                event_type=event_type,
                payload=event,
            )
        except IntegrityError:
            # Duplicate Stripe event (same event id) => already processed.
            logger.info(
                "Stripe webhook duplicate event skipped",
                extra={
                    "event_type": event_type,
                    "stripe_session_id": str(session_id),
                    "stripe_event_id": str(event_id),
                },
            )
            return

        payment = Payment.objects.select_for_update().filter(
            provider=Payment.Provider.STRIPE,
            external_id=str(session_id),
        ).first()
        if not payment:
            logger.warning(
                "Stripe webhook for unknown session",
                extra={
                    "event_type": event_type,
                    "stripe_session_id": str(session_id),
                    "stripe_event_id": str(event_id),
                },
            )
            return

        payment.raw_response = event
        payment.save(update_fields=["raw_response", "updated"])

        logger.info(
            "Stripe webhook accepted",
            extra={
                "order_public_id": str(payment.order.public_id),
                "payment_id": payment.id,
                "event_type": event_type,
                "stripe_session_id": str(session_id),
                "stripe_event_id": str(event_id),
            },
        )

        if event_type == "checkout.session.completed":
            _apply_payment_status(payment, Payment.Status.PAID)
        elif event_type in {"checkout.session.expired"}:
            _apply_payment_status(payment, Payment.Status.CANCELED)
        elif event_type in {"checkout.session.async_payment_failed"}:
            _apply_payment_status(payment, Payment.Status.FAILED)
