from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse

from apps.orders.models import Order
from apps.orders.services import create_order_from_cart
from apps.orders.use_cases.authorize_order_access import build_guest_payment_start_redirect


@dataclass(frozen=True)
class CheckoutSubmitDecision:
    redirect_url: str | None = None
    form_error: str | None = None


def build_checkout_initial(request) -> dict:
    """
    Build initial form data for checkout without coupling this logic to views.
    """
    initial = {
        "country": "SK",
        "shipping_method": Order.ShippingMethod.DPD_HOME,
    }
    if request.user.is_authenticated:
        initial["email"] = request.user.email
        initial["full_name"] = request.user.get_full_name()
    return initial


def _present_checkout_error(message: str) -> str:
    if message == "One or more variants are unavailable":
        return "К сожалению, один из товаров в корзине больше недоступен. Проверьте состав корзины."
    if message.startswith("Not enough stock for "):
        return "К сожалению, товар из вашей корзины уже закончился или доступного количества больше нет."
    if message == "Cannot create order from empty cart":
        return "Ваша корзина пуста."
    return message


def process_checkout_submission(request, cart, cleaned_data: dict) -> CheckoutSubmitDecision:
    """
    Create order from cart and return a pure decision for HTTP layer.
    """
    try:
        order = create_order_from_cart(request, cart, cleaned_data)
    except ValueError as exc:
        return CheckoutSubmitDecision(form_error=_present_checkout_error(str(exc)))

    # Guest checkout requires an access token bound to session.
    if not order.user_id:
        return CheckoutSubmitDecision(redirect_url=build_guest_payment_start_redirect(request, order))

    return CheckoutSubmitDecision(
        redirect_url=reverse("orders:payment_start", kwargs={"public_id": order.public_id})
    )
