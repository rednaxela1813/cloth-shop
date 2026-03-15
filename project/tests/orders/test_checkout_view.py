import pytest
from django.urls import reverse

from apps.cart.services import get_or_create_cart
from apps.products.models import Product, ProductVariant


pytestmark = pytest.mark.django_db


def test_checkout_view_shows_field_specific_errors_and_highlights_invalid_inputs(client):
    product = Product.objects.create(name="Jacket", is_active=True)
    variant = ProductVariant.objects.create(
        product=product,
        size="33",
        color="White",
        sku="JACKET-WHT-33",
        price="110.00",
        stock=2,
        is_active=True,
    )

    request = client.get(reverse("orders:checkout")).wsgi_request
    cart = get_or_create_cart(request)
    cart.items.create(variant=variant, quantity=1)

    response = client.post(
        reverse("orders:checkout"),
        data={
            "full_name": "",
            "email": "invalid-email",
            "phone": "0947914542",
            "country": "SK",
            "shipping_method": "paketa_pickup",
            "region": "Oblast",
            "city": "Ziar nad Hronom",
            "postal_code": "",
            "address_line1": "",
            "address_line2": "",
        },
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Проверьте выделенные поля ниже." in html
    assert 'href="#id_full_name"' in html
    assert 'href="#id_email"' in html
    assert 'aria-invalid="true"' in html
    assert "border-red-400" in html
