import pytest
from django.contrib.auth import get_user_model

from apps.cart.services import get_or_create_cart
from apps.orders.use_cases.checkout import build_checkout_initial, process_checkout_submission


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
    assert decision.form_error == "Cannot create order from empty cart"
