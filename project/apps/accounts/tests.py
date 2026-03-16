import pytest
from django.urls import reverse

from apps.cart.models import Cart, CartItem
from apps.orders.models import Address, Order
from apps.products.models import Product, ProductVariant

pytestmark = pytest.mark.django_db


def _make_user(*, django_user_model, email="user@example.com", password="pass12345"):
    return django_user_model.objects.create_user(email=email, password=password)


def _make_address(*, user, suffix="1"):
    return Address.objects.create(
        user=user,
        full_name=f"User {suffix}",
        email=user.email,
        country="SK",
        city="Bratislava",
        address_line1=f"Main {suffix}",
    )


def test_account_dashboard_requires_login(client):
    response = client.get(reverse("accounts:dashboard"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response["Location"]


def test_account_orders_requires_login(client):
    response = client.get(reverse("accounts:orders"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response["Location"]


def test_account_login_renders_form(client):
    response = client.get(reverse("accounts:login"))

    assert response.status_code == 200
    assert "form" in response.context


def test_account_register_renders_form(client):
    response = client.get(reverse("accounts:register"))

    assert response.status_code == 200
    assert "form" in response.context


def test_account_login_authenticates_with_email(client, django_user_model):
    user = _make_user(django_user_model=django_user_model)

    response = client.post(
        reverse("accounts:login"),
        {"email": "user@example.com", "password": "pass12345"},
    )

    assert response.status_code == 302
    assert response["Location"].endswith(reverse("accounts:dashboard"))

    dashboard = client.get(reverse("accounts:dashboard"))
    assert dashboard.status_code == 200
    assert dashboard.wsgi_request.user == user


def test_account_login_redirects_to_next_when_provided(client, django_user_model):
    _make_user(django_user_model=django_user_model)

    response = client.post(
        reverse("accounts:login"),
        {
            "email": "user@example.com",
            "password": "pass12345",
            "next": reverse("accounts:orders"),
        },
    )

    assert response.status_code == 302
    assert response["Location"].endswith(reverse("accounts:orders"))


def test_account_login_shows_error_for_invalid_credentials(client, django_user_model):
    _make_user(django_user_model=django_user_model)

    response = client.post(
        reverse("accounts:login"),
        {"email": "user@example.com", "password": "wrong-pass"},
    )

    assert response.status_code == 200
    assert "Nesprávny email alebo heslo." in response.content.decode("utf-8")


def test_account_login_redirects_authenticated_user_to_dashboard(client, django_user_model):
    _make_user(django_user_model=django_user_model)
    client.login(email="user@example.com", password="pass12345")

    response = client.get(reverse("accounts:login"))

    assert response.status_code == 302
    assert response["Location"].endswith(reverse("accounts:dashboard"))


def test_account_register_creates_customer_with_minimal_permissions(client, django_user_model):
    response = client.post(
        reverse("accounts:register"),
        {
            "email": "newuser@example.com",
            "password1": "pass12345Strong",
            "password2": "pass12345Strong",
        },
    )

    assert response.status_code == 302
    assert response["Location"].endswith(reverse("accounts:dashboard"))

    user = django_user_model.objects.get(email="newuser@example.com")
    assert user.is_staff is False
    assert user.is_superuser is False
    dashboard = client.get(reverse("accounts:dashboard"))
    assert dashboard.status_code == 200
    assert dashboard.wsgi_request.user == user


def test_account_register_redirects_to_next_when_provided(client):
    response = client.post(
        reverse("accounts:register"),
        {
            "email": "nextuser@example.com",
            "password1": "pass12345Strong",
            "password2": "pass12345Strong",
            "next": reverse("accounts:orders"),
        },
    )

    assert response.status_code == 302
    assert response["Location"].endswith(reverse("accounts:orders"))


def test_account_register_rejects_duplicate_email(client, django_user_model):
    _make_user(django_user_model=django_user_model, email="dupe@example.com")

    response = client.post(
        reverse("accounts:register"),
        {
            "email": "dupe@example.com",
            "password1": "pass12345Strong",
            "password2": "pass12345Strong",
        },
    )

    assert response.status_code == 200
    assert "Používateľ s týmto emailom už existuje." in response.content.decode("utf-8")


def test_account_register_rejects_mismatched_passwords(client):
    response = client.post(
        reverse("accounts:register"),
        {
            "email": "mismatch@example.com",
            "password1": "pass12345Strong",
            "password2": "different12345",
        },
    )

    assert response.status_code == 200
    assert "Heslá sa musia zhodovať." in response.content.decode("utf-8")


def test_account_register_redirects_authenticated_user_to_dashboard(client, django_user_model):
    _make_user(django_user_model=django_user_model)
    client.login(email="user@example.com", password="pass12345")

    response = client.get(reverse("accounts:register"))

    assert response.status_code == 302
    assert response["Location"].endswith(reverse("accounts:dashboard"))


def test_account_logout_logs_user_out(client, django_user_model):
    _make_user(django_user_model=django_user_model)
    client.login(email="user@example.com", password="pass12345")

    response = client.get(reverse("accounts:logout"))

    assert response.status_code == 302
    assert response["Location"].endswith(reverse("pages:home"))
    follow_up = client.get(reverse("accounts:dashboard"))
    assert follow_up.status_code == 302


def test_account_orders_lists_only_current_user_orders(client, django_user_model):
    user = _make_user(django_user_model=django_user_model, email="owner@example.com")
    other = _make_user(django_user_model=django_user_model, email="other@example.com")

    user_address = _make_address(user=user, suffix="1")
    other_address = _make_address(user=other, suffix="2")
    own_order = Order.objects.create(user=user, email=user.email, shipping_address=user_address)
    Order.objects.create(user=other, email=other.email, shipping_address=other_address)

    client.login(email="owner@example.com", password="pass12345")
    response = client.get(reverse("accounts:orders"))

    assert response.status_code == 200
    orders = list(response.context["orders"])
    assert orders == [own_order]


def test_account_dashboard_includes_active_cart_metrics(client, django_user_model):
    user = _make_user(django_user_model=django_user_model, email="cartuser@example.com")
    product = Product.objects.create(name="Boots")
    variant = ProductVariant.objects.create(
        product=product,
        size="42",
        color="Black",
        sku="ACC-BOOT-42-BLK",
        price="25.00",
        stock=10,
        is_active=True,
    )
    cart = Cart.objects.create(user=user, is_active=True)
    CartItem.objects.create(cart=cart, variant=variant, quantity=2)

    client.login(email="cartuser@example.com", password="pass12345")
    response = client.get(reverse("accounts:dashboard"))

    assert response.status_code == 200
    assert response.context["cart_items_count"] == 2
    assert str(response.context["cart_subtotal"]) == "50.00"


def test_account_dashboard_defaults_cart_metrics_to_zero_without_active_cart(client, django_user_model):
    user = _make_user(django_user_model=django_user_model, email="nocart@example.com")

    client.login(email="nocart@example.com", password="pass12345")
    response = client.get(reverse("accounts:dashboard"))

    assert response.status_code == 200
    assert response.context["cart_items_count"] == 0
    assert response.context["cart_subtotal"] == 0


def test_account_dashboard_exposes_order_counts_and_recent_orders(client, django_user_model):
    user = _make_user(django_user_model=django_user_model, email="orders@example.com")
    address = _make_address(user=user, suffix="7")
    older = Order.objects.create(
        user=user,
        email=user.email,
        shipping_address=address,
        status=Order.Status.PAID,
    )
    newer = Order.objects.create(
        user=user,
        email=user.email,
        shipping_address=address,
        status=Order.Status.PENDING,
    )

    client.login(email="orders@example.com", password="pass12345")
    response = client.get(reverse("accounts:dashboard"))

    assert response.status_code == 200
    assert response.context["orders_count"] == 2
    assert response.context["pending_orders_count"] == 1
    assert response.context["recent_orders"] == [newer, older]
