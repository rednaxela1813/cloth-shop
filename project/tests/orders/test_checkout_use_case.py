import json

import pytest
from django.contrib.auth import get_user_model

from apps.cart.services import get_or_create_cart
from apps.orders.models import Order
from apps.orders.services import create_order_from_cart
from apps.orders.use_cases.checkout import build_checkout_initial, process_checkout_submission
from apps.products.models import Product, ProductVariant


pytestmark = pytest.mark.django_db


def test_build_checkout_initial_for_authenticated_user():
    user = get_user_model().objects.create_user(
        email="initial@example.com",
        password="pass12345",
        first_name="Jane",
        last_name="Doe",
    )

    class DummyRequest:
        pass

    request = DummyRequest()
    request.user = user

    initial = build_checkout_initial(request)
    assert initial["email"] == "initial@example.com"
    assert initial["full_name"] == "Jane Doe"
    assert initial["country"] == "SK"
    assert initial["shipping_method"] == Order.ShippingMethod.DPD_HOME


def test_process_checkout_submission_returns_form_error_for_empty_cart(client, django_user_model):
    user = django_user_model.objects.create_user(email="buyer@example.com", password="pass12345")
    client.force_login(user)
    request = client.get("/checkout/").wsgi_request
    # The checkout page access may already initialize an active cart for this user.
    # Reuse it instead of creating a second active cart (unique constraint).
    cart = get_or_create_cart(request)

    decision = process_checkout_submission(
        request,
        cart,
        {
            "full_name": "Buyer",
            "email": "buyer@example.com",
            "phone": "",
            "country": "SK",
            "region": "",
            "city": "Bratislava",
            "postal_code": "",
            "address_line1": "Main 1",
            "address_line2": "",
        },
    )

    assert decision.redirect_url is None
    assert decision.form_error == "Ваша корзина пуста."


def test_process_checkout_submission_returns_customer_message_for_out_of_stock(client, django_user_model):
    user = django_user_model.objects.create_user(email="buyer@example.com", password="pass12345")
    client.force_login(user)

    request = client.get("/checkout/").wsgi_request
    cart = get_or_create_cart(request)
    product = Product.objects.create(name="Jacket", is_active=True)
    variant = ProductVariant.objects.create(
        product=product,
        size="33",
        color="White",
        sku="JACKET-WHT-33-CHECKOUT",
        price="110.00",
        stock=0,
        is_active=True,
    )
    cart.items.create(variant=variant, quantity=1)

    decision = process_checkout_submission(
        request,
        cart,
        {
            "full_name": "Buyer",
            "email": "buyer@example.com",
            "phone": "",
            "country": "SK",
            "shipping_method": Order.ShippingMethod.DPD_HOME,
            "region": "",
            "city": "Bratislava",
            "postal_code": "",
            "address_line1": "Main 1",
            "address_line2": "",
        },
    )

    assert decision.redirect_url is None
    assert decision.form_error == "К сожалению, товар из вашей корзины уже закончился или доступного количества больше нет."


def test_create_order_from_cart_persists_packeta_pickup_point_snapshot(client):
    request = client.get("/checkout/").wsgi_request
    cart = get_or_create_cart(request)
    product = Product.objects.create(name="Coat", is_active=True)
    variant = ProductVariant.objects.create(
        product=product,
        size="M",
        color="Blue",
        sku="COAT-BLU-M",
        price="150.00",
        stock=2,
        is_active=True,
    )
    cart.items.create(variant=variant, quantity=1)

    point_payload = {
        "id": "12345",
        "name": "Paketa Central",
        "city": "Bratislava",
        "street": "Main 7",
        "zip": "81101",
        "carrierId": "packeta",
        "carrierPickupPointId": "pickup-77",
        "formatedValue": "Paketa Central, Main 7, Bratislava",
    }

    order = create_order_from_cart(
        request,
        cart,
        {
            "full_name": "Buyer",
            "email": "buyer@example.com",
            "phone": "",
            "country": "SK",
            "shipping_method": Order.ShippingMethod.PAKETA_PICKUP,
            "region": "",
            "city": "",
            "postal_code": "",
            "address_line1": "",
            "address_line2": "",
            "packeta_point_id": "12345",
            "packeta_point_name": "Paketa Central",
            "packeta_point_address": "Paketa Central, Main 7, Bratislava",
            "packeta_carrier_id": "packeta",
            "packeta_carrier_pickup_point_id": "pickup-77",
            "packeta_point_json": json.dumps(point_payload),
        },
    )

    assert order.shipping_method == Order.ShippingMethod.PAKETA_PICKUP
    assert order.packeta_point_id == "12345"
    assert order.packeta_point_name == "Paketa Central"
    assert order.packeta_point_address == "Paketa Central, Main 7, Bratislava"
    assert order.packeta_carrier_id == "packeta"
    assert order.packeta_carrier_pickup_point_id == "pickup-77"
    assert order.packeta_point_raw["city"] == "Bratislava"
    assert order.shipping_address.city == "Bratislava"
    assert order.shipping_address.postal_code == "81101"
    assert order.shipping_address.address_line1 == "Paketa Central, Main 7, Bratislava"
