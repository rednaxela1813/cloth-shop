import pytest
from django.test import RequestFactory

from apps.products.models import Product, ProductImage, ProductVariant
from apps.products.use_cases.product_pages import build_product_detail_result, build_product_list_context

pytestmark = pytest.mark.django_db


def test_build_product_list_context_filters_active_and_sorts_by_price_asc():
    rf = RequestFactory()
    request = rf.get("/shop/?sort=price_asc&page=1")

    low = Product.objects.create(name="Low", price="999.00", is_active=True)
    high = Product.objects.create(name="High", price="1.00", is_active=True)
    Product.objects.create(name="Inactive", price="1.00", is_active=False)
    ProductVariant.objects.create(product=low, size="S", color="Black", sku="LOW-S-BLK", price="10.00", stock=2, is_active=True)
    ProductVariant.objects.create(product=high, size="S", color="Black", sku="HIGH-S-BLK", price="20.00", stock=2, is_active=True)

    context = build_product_list_context(request=request, page_size=12)

    assert context["products_count"] == 2
    assert list(context["page_obj"].object_list) == [low, high]


def test_build_product_detail_result_returns_redirect_for_wrong_slug():
    rf = RequestFactory()
    product = Product.objects.create(name="Silk Dress", price="100.00", is_active=True)
    request = rf.get(f"/shop/{product.public_id}/wrong-slug/")

    result = build_product_detail_result(request=request, public_id=product.public_id, slug="wrong-slug")

    assert result.redirect_slug == product.slug
    assert result.context is None
    assert result.product.id == product.id


def test_build_product_detail_result_builds_context_with_primary_and_variant_selection():
    rf = RequestFactory()
    product = Product.objects.create(name="Variant Dress", brand="Gucci", price="220.00", is_active=True)
    ProductImage.objects.create(product=product, alt="secondary", sort_order=2, is_primary=False)
    primary = ProductImage.objects.create(product=product, alt="primary", sort_order=1, is_primary=True)

    low_stock = ProductVariant.objects.create(
        product=product,
        size="S",
        color="Black",
        sku="VD-BLK-S-UC",
        price="220.00",
        stock=0,
        is_active=True,
    )
    in_stock = ProductVariant.objects.create(
        product=product,
        size="M",
        color="Black",
        sku="VD-BLK-M-UC",
        price="230.00",
        stock=3,
        is_active=True,
    )
    request = rf.get(f"/shop/{product.public_id}/{product.slug}/")

    # Проверяем use-case напрямую, без view-слоя.
    result = build_product_detail_result(request=request, public_id=product.public_id, slug=product.slug)

    assert result.redirect_slug is None
    assert result.context["primary_image"].id == primary.id
    assert result.context["selected_variant"].id == in_stock.id
    assert [item["public_id"] for item in result.context["variant_payload"]] == [
        str(in_stock.public_id),
        str(low_stock.public_id),
    ]
