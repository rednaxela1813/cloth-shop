from decimal import Decimal

import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from apps.products.admin import ProductVariantAdmin, StockLevelFilter
from apps.products.models import Product, ProductVariant

pytestmark = pytest.mark.django_db


def _variant(*, product, sku, stock):
    return ProductVariant.objects.create(
        product=product,
        size=sku,
        color="Black",
        sku=sku,
        price=Decimal("25.00"),
        stock=stock,
    )


def test_stock_level_filter_returns_low_stock_variants():
    product = Product.objects.create(name="Admin Product")
    out = _variant(product=product, sku="OUT", stock=0)
    low = _variant(product=product, sku="LOW", stock=2)
    available = _variant(product=product, sku="AVAILABLE", stock=8)
    request = RequestFactory().get("/admin/products/productvariant/", {"stock_level": "low"})
    model_admin = ProductVariantAdmin(ProductVariant, AdminSite())
    stock_filter = StockLevelFilter(request, {"stock_level": "low"}, ProductVariant, model_admin)
    stock_filter.used_parameters = {"stock_level": "low"}

    result = list(stock_filter.queryset(request, ProductVariant.objects.order_by("sku")))

    assert result == [low]
    assert out not in result
    assert available not in result


def test_product_variant_admin_stock_status_labels():
    product = Product.objects.create(name="Admin Product")
    model_admin = ProductVariantAdmin(ProductVariant, AdminSite())

    assert model_admin.stock_status(_variant(product=product, sku="OUT", stock=0)) == "Vypredané"
    assert model_admin.stock_status(_variant(product=product, sku="LOW", stock=3)) == "Nízky stav"
    assert model_admin.stock_status(_variant(product=product, sku="AVAILABLE", stock=4)) == "Na sklade"
