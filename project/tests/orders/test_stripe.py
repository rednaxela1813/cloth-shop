from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.signing import TimestampSigner
from django.urls import reverse

from apps.orders.access import TOKEN_SALT
from apps.orders.models import Address, Order, OrderItem, Payment, ProcessedStripeEvent
from apps.products.models import Product, ProductVariant

pytestmark = pytest.mark.django_db


class _DummyStripeSession:
    def __init__(self, session_id: str, url: str):
        self.id = session_id
        self.url = url

    def to_dict_recursive(self):
        return {"id": self.id, "url": self.url}


def _make_order(user=None):
    product = Product.objects.create(name="Stripe Product", price="10.00")
    ProductVariant.objects.create(
        product=product,
        size="M",
        color="Black",
        sku="STRIPE-BLK-M",
        price="10.00",
        stock=3,
    )
    address = Address.objects.create(
        full_name="Buyer",
        email="buyer@example.com",
        country="SK",
        city="Bratislava",
        address_line1="Main 1",
    )
    return Order.objects.create(
        user=user,
        email="buyer@example.com",
        shipping_address=address,
        subtotal=Decimal("10.00"),
        shipping_cost=Decimal("0.00"),
        total=Decimal("10.00"),
        currency="EUR",
    )


def _make_reserved_order_with_item(*, stock_before_reservation=5, quantity=2):
    product = Product.objects.create(name="Stripe Reserved Product", price="10.00")
    variant = ProductVariant.objects.create(
        product=product,
        size="L",
        color="Blue",
        sku=f"STRIPE-RSV-{stock_before_reservation}-{quantity}",
        price="10.00",
        stock=stock_before_reservation - quantity,
    )
    address = Address.objects.create(
        full_name="Buyer",
        email="buyer@example.com",
        country="SK",
        city="Bratislava",
        address_line1="Main 1",
    )
    order = Order.objects.create(
        email="buyer@example.com",
        shipping_address=address,
        subtotal=Decimal("10.00"),
        shipping_cost=Decimal("0.00"),
        total=Decimal("10.00"),
        currency="EUR",
    )
    OrderItem.objects.create(
        order=order,
        variant=variant,
        quantity=quantity,
        product_name=product.name,
        sku=variant.sku,
        size=variant.size,
        color=variant.color,
        unit_price=Decimal("10.00"),
        line_total=Decimal("20.00"),
    )
    return order, variant


def test_payment_start_redirects_to_gateway(client, monkeypatch, settings):
    settings.STRIPE_SECRET_KEY = "sk_test_123"

    order = _make_order()
    session = client.session
    session.save()
    guest_token = TimestampSigner(salt=TOKEN_SALT).sign(f"{order.public_id}:{session.session_key}")

    long_session_id = "cs_test_" + ("x" * 90)
    long_gateway_url = f"https://checkout.stripe.com/pay/{long_session_id}?k=" + ("y" * 260)

    def fake_session_create(**kwargs):
        assert kwargs["mode"] == "payment"
        return _DummyStripeSession(
            session_id=long_session_id,
            url=long_gateway_url,
        )

    monkeypatch.setattr("apps.orders.services.stripe_gateway.create_checkout_session", lambda **kwargs: fake_session_create(**kwargs))

    response = client.get(
        reverse("orders:payment_start", kwargs={"public_id": order.public_id}),
        {"access_token": guest_token},
    )

    assert response.status_code == 302
    assert response["Location"] == long_gateway_url

    payment = order.payments.get()
    assert payment.external_id == long_session_id
    assert payment.gateway_url == long_gateway_url
    assert payment.status == Payment.Status.PENDING


def test_payment_start_redirects_to_error_gateway_on_stripe_error(client, monkeypatch, settings):
    settings.STRIPE_SECRET_KEY = "sk_test_123"
    order = _make_order()
    session = client.session
    session.save()
    guest_token = TimestampSigner(salt=TOKEN_SALT).sign(f"{order.public_id}:{session.session_key}")

    import stripe as stripe_sdk

    monkeypatch.setattr(
        "apps.orders.services.stripe_gateway.create_checkout_session",
        lambda **kwargs: (_ for _ in ()).throw(stripe_sdk.APIConnectionError("network")),
    )

    response = client.get(
        reverse("orders:payment_start", kwargs={"public_id": order.public_id}),
        {"access_token": guest_token},
    )

    assert response.status_code == 302
    assert response["Location"].endswith("/checkout/payment/return/?status=error_gateway")


def test_payment_start_restores_stock_and_cancels_order_on_gateway_error(client, monkeypatch, settings):
    settings.STRIPE_SECRET_KEY = "sk_test_123"
    order, variant = _make_reserved_order_with_item(stock_before_reservation=5, quantity=2)
    session = client.session
    session.save()
    guest_token = TimestampSigner(salt=TOKEN_SALT).sign(f"{order.public_id}:{session.session_key}")

    import stripe as stripe_sdk

    monkeypatch.setattr(
        "apps.orders.services.stripe_gateway.create_checkout_session",
        lambda **kwargs: (_ for _ in ()).throw(stripe_sdk.APIConnectionError("network")),
    )

    response = client.get(
        reverse("orders:payment_start", kwargs={"public_id": order.public_id}),
        {"access_token": guest_token},
    )

    assert response.status_code == 302
    assert response["Location"].endswith("/checkout/payment/return/?status=error_gateway")

    order.refresh_from_db()
    variant.refresh_from_db()
    assert order.status == Order.Status.CANCELED
    assert variant.stock == 5


def test_stripe_webhook_marks_order_paid(client, monkeypatch, settings):
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test_123"

    order = _make_order()
    payment = Payment.objects.create(
        order=order,
        amount=Decimal("10.00"),
        currency="EUR",
        external_id="cs_test_1001",
        status=Payment.Status.PENDING,
        provider=Payment.Provider.STRIPE,
    )

    def fake_construct_event(payload, sig_header, secret):
        assert payload
        assert sig_header == "sig-header"
        assert secret == "whsec_test_123"
        return {
            "id": "evt_paid_1",
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_test_1001"}},
        }

    monkeypatch.setattr("apps.orders.use_cases.handle_stripe_webhook.stripe_gateway.construct_webhook_event", fake_construct_event)

    response = client.post(
        reverse("orders:stripe_webhook"),
        data=b'{"id":"evt_1"}',
        content_type="application/json",
        headers={"Stripe-Signature": "sig-header"},
    )

    assert response.status_code == 200
    payment.refresh_from_db()
    order.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    assert order.status == Order.Status.PAID


def test_stripe_webhook_rejects_missing_signature(client, settings):
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test_123"
    response = client.post(
        reverse("orders:stripe_webhook"),
        data=b'{"id":"evt_1"}',
        content_type="application/json",
    )
    assert response.status_code == 400


def test_stripe_webhook_rejects_invalid_signature(client, monkeypatch, settings):
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test_123"

    import stripe as stripe_sdk

    def raise_bad_signature(payload, sig_header, secret):
        raise stripe_sdk.SignatureVerificationError("invalid", "sig-header")

    monkeypatch.setattr("apps.orders.use_cases.handle_stripe_webhook.stripe_gateway.construct_webhook_event", raise_bad_signature)
    response = client.post(
        reverse("orders:stripe_webhook"),
        data=b'{"id":"evt_1"}',
        content_type="application/json",
        headers={"Stripe-Signature": "sig-header"},
    )
    assert response.status_code == 400


def test_stripe_webhook_is_idempotent_for_duplicate_event_id(client, monkeypatch, settings):
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test_123"

    order = _make_order()
    payment = Payment.objects.create(
        order=order,
        amount=Decimal("10.00"),
        currency="EUR",
        external_id="cs_test_1002",
        status=Payment.Status.PENDING,
        provider=Payment.Provider.STRIPE,
    )

    def fake_construct_event(payload, sig_header, secret):
        return {
            "id": "evt_duplicate_1",
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_test_1002"}},
        }

    monkeypatch.setattr("apps.orders.use_cases.handle_stripe_webhook.stripe_gateway.construct_webhook_event", fake_construct_event)

    for _ in range(2):
        response = client.post(
            reverse("orders:stripe_webhook"),
            data=b'{"id":"evt_duplicate_1"}',
            content_type="application/json",
            headers={"Stripe-Signature": "sig-header"},
        )
        assert response.status_code == 200

    payment.refresh_from_db()
    order.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    assert order.status == Order.Status.PAID
    assert ProcessedStripeEvent.objects.filter(stripe_event_id="evt_duplicate_1").count() == 1


def test_stripe_webhook_marks_order_canceled_on_expired(client, monkeypatch, settings):
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test_123"
    order = _make_order()
    payment = Payment.objects.create(
        order=order,
        amount=Decimal("10.00"),
        currency="EUR",
        external_id="cs_test_expired",
        status=Payment.Status.PENDING,
        provider=Payment.Provider.STRIPE,
    )

    monkeypatch.setattr(
        "apps.orders.use_cases.handle_stripe_webhook.stripe_gateway.construct_webhook_event",
        lambda payload, sig_header, secret: {
            "id": "evt_expired_1",
            "type": "checkout.session.expired",
            "data": {"object": {"id": "cs_test_expired"}},
        },
    )

    response = client.post(
        reverse("orders:stripe_webhook"),
        data=b'{"id":"evt_expired_1"}',
        content_type="application/json",
        headers={"Stripe-Signature": "sig-header"},
    )
    assert response.status_code == 200
    payment.refresh_from_db()
    order.refresh_from_db()
    assert payment.status == Payment.Status.CANCELED
    assert order.status == Order.Status.CANCELED


def test_stripe_webhook_expired_restores_reserved_stock(client, monkeypatch, settings):
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test_123"
    order, variant = _make_reserved_order_with_item(stock_before_reservation=7, quantity=3)
    Payment.objects.create(
        order=order,
        amount=Decimal("30.00"),
        currency="EUR",
        external_id="cs_test_expired_stock",
        status=Payment.Status.PENDING,
        provider=Payment.Provider.STRIPE,
    )

    monkeypatch.setattr(
        "apps.orders.use_cases.handle_stripe_webhook.stripe_gateway.construct_webhook_event",
        lambda payload, sig_header, secret: {
            "id": "evt_expired_stock_1",
            "type": "checkout.session.expired",
            "data": {"object": {"id": "cs_test_expired_stock"}},
        },
    )

    response = client.post(
        reverse("orders:stripe_webhook"),
        data=b'{"id":"evt_expired_stock_1"}',
        content_type="application/json",
        headers={"Stripe-Signature": "sig-header"},
    )
    assert response.status_code == 200

    order.refresh_from_db()
    variant.refresh_from_db()
    assert order.status == Order.Status.CANCELED
    assert variant.stock == 7


def test_stripe_webhook_marks_payment_failed_on_async_failed(client, monkeypatch, settings):
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test_123"
    order = _make_order()
    payment = Payment.objects.create(
        order=order,
        amount=Decimal("10.00"),
        currency="EUR",
        external_id="cs_test_async_failed",
        status=Payment.Status.PENDING,
        provider=Payment.Provider.STRIPE,
    )

    monkeypatch.setattr(
        "apps.orders.use_cases.handle_stripe_webhook.stripe_gateway.construct_webhook_event",
        lambda payload, sig_header, secret: {
            "id": "evt_async_failed_1",
            "type": "checkout.session.async_payment_failed",
            "data": {"object": {"id": "cs_test_async_failed"}},
        },
    )

    response = client.post(
        reverse("orders:stripe_webhook"),
        data=b'{"id":"evt_async_failed_1"}',
        content_type="application/json",
        headers={"Stripe-Signature": "sig-header"},
    )
    assert response.status_code == 200
    payment.refresh_from_db()
    order.refresh_from_db()
    assert payment.status == Payment.Status.FAILED
    assert order.status == Order.Status.CANCELED


def test_payment_start_denies_foreign_authenticated_user(client, settings):
    owner = get_user_model().objects.create_user(email="owner@example.com", password="pass12345")
    intruder = get_user_model().objects.create_user(email="intruder@example.com", password="pass12345")
    order = _make_order(user=owner)

    client.force_login(intruder)
    response = client.get(reverse("orders:payment_start", kwargs={"public_id": order.public_id}))
    assert response.status_code == 404


def test_checkout_success_denies_foreign_authenticated_user(client):
    owner = get_user_model().objects.create_user(email="owner2@example.com", password="pass12345")
    intruder = get_user_model().objects.create_user(email="intruder2@example.com", password="pass12345")
    order = _make_order(user=owner)

    client.force_login(intruder)
    response = client.get(reverse("orders:success", kwargs={"public_id": order.public_id}))
    assert response.status_code == 404


def test_checkout_success_for_guest_requires_signed_token(client):
    order = _make_order()

    denied = client.get(reverse("orders:success", kwargs={"public_id": order.public_id}))
    assert denied.status_code == 404

    session = client.session
    session.save()
    token = TimestampSigner(salt=TOKEN_SALT).sign(f"{order.public_id}:{session.session_key}")
    allowed = client.get(reverse("orders:success", kwargs={"public_id": order.public_id}), {"access_token": token})
    assert allowed.status_code == 200


def test_payment_start_for_guest_requires_signed_token(client):
    order = _make_order()
    response = client.get(reverse("orders:payment_start", kwargs={"public_id": order.public_id}))
    assert response.status_code == 404
