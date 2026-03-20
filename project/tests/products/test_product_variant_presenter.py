import pytest

from apps.products.models import Product, ProductVariant
from apps.products.services.product_variant_presenter import build_variant_selection_state

pytestmark = pytest.mark.django_db


def test_build_variant_selection_state_selects_lowest_priced_in_stock_variant():
    product = Product.objects.create(name="Variant Tee", is_active=True)
    cheaper_out_of_stock = ProductVariant.objects.create(
        product=product,
        size="S",
        color="Black",
        sku="VT-BLK-S-PRES",
        price="100.00",
        stock=0,
        is_active=True,
    )
    cheapest_in_stock = ProductVariant.objects.create(
        product=product,
        size="M",
        color="Black",
        sku="VT-BLK-M-PRES",
        price="110.00",
        stock=2,
        is_active=True,
    )

    state = build_variant_selection_state(product=product)

    assert [v.id for v in state.active_variants] == [cheapest_in_stock.id, cheaper_out_of_stock.id]
    assert state.selected_variant.id == cheapest_in_stock.id
    assert state.variant_payload[0]["public_id"] == str(cheapest_in_stock.public_id)
    assert state.variant_payload[1]["public_id"] == str(cheaper_out_of_stock.public_id)


def test_build_variant_selection_state_returns_none_when_no_active_variants():
    product = Product.objects.create(name="No Variant Item", is_active=True)
    ProductVariant.objects.create(
        product=product,
        size="L",
        color="Blue",
        sku="NVI-BLU-L-PRES",
        price="50.00",
        stock=10,
        is_active=False,
    )

    state = build_variant_selection_state(product=product)

    assert state.active_variants == []
    assert state.selected_variant is None
    assert state.variant_payload == []


def test_build_variant_selection_state_prefers_requested_variant_from_query_param():
    product = Product.objects.create(name="Variant Tee", is_active=True)
    default_variant = ProductVariant.objects.create(
        product=product,
        size="S",
        color="Black",
        sku="VT-BLK-S-REQ",
        price="100.00",
        stock=2,
        is_active=True,
    )
    requested_variant = ProductVariant.objects.create(
        product=product,
        size="M",
        color="Black",
        sku="VT-BLK-M-REQ",
        price="120.00",
        stock=1,
        is_active=True,
    )

    state = build_variant_selection_state(
        product=product,
        variant_public_id=str(requested_variant.public_id),
    )

    assert state.selected_variant.id == requested_variant.id
    assert state.selected_variant.id != default_variant.id
