import pytest

from apps.products.models import Product, ProductVariant
from apps.products.services.product_variant_presenter import build_active_variants_payload

pytestmark = pytest.mark.django_db


def test_build_active_variants_payload_selects_first_in_stock_variant():
    product = Product.objects.create(name="Variant Tee", price="100.00", is_active=True)
    out_of_stock = ProductVariant.objects.create(
        product=product,
        size="S",
        color="Black",
        sku="VT-BLK-S-PRES",
        price="100.00",
        stock=0,
        is_active=True,
    )
    in_stock = ProductVariant.objects.create(
        product=product,
        size="M",
        color="Black",
        sku="VT-BLK-M-PRES",
        price="110.00",
        stock=2,
        is_active=True,
    )

    active_variants, selected_variant, payload = build_active_variants_payload(product=product)

    assert [v.id for v in active_variants] == [in_stock.id, out_of_stock.id]
    assert selected_variant.id == in_stock.id
    assert payload[0]["public_id"] == str(in_stock.public_id)
    assert payload[1]["public_id"] == str(out_of_stock.public_id)


def test_build_active_variants_payload_returns_none_when_no_active_variants():
    product = Product.objects.create(name="No Variant Item", price="50.00", is_active=True)
    ProductVariant.objects.create(
        product=product,
        size="L",
        color="Blue",
        sku="NVI-BLU-L-PRES",
        price="50.00",
        stock=10,
        is_active=False,
    )

    active_variants, selected_variant, payload = build_active_variants_payload(product=product)

    assert active_variants == []
    assert selected_variant is None
    assert payload == []
