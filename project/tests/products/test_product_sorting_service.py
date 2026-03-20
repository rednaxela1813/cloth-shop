import pytest
from django.test import RequestFactory

from apps.products.models import Product, ProductVariant
from apps.products.services.product_sorting_service import sort_products_queryset

pytestmark = pytest.mark.django_db


def test_sort_products_queryset_price_asc():
    rf = RequestFactory()
    request = rf.get("/shop/?sort=price_asc")
    low = Product.objects.create(name="Low", is_active=True)
    high = Product.objects.create(name="High", is_active=True)
    ProductVariant.objects.create(
        product=low, size="M", color="Black", sku="LOW-M-BLK", price="10.00", stock=1, is_active=True
    )
    ProductVariant.objects.create(
        product=high, size="M", color="Black", sku="HIGH-M-BLK", price="20.00", stock=1, is_active=True
    )

    qs, sort = sort_products_queryset(request=request, queryset=Product.objects.all())

    assert sort == "price_asc"
    assert list(qs) == [low, high]


def test_sort_products_queryset_price_desc():
    rf = RequestFactory()
    request = rf.get("/shop/?sort=price_desc")
    low = Product.objects.create(name="Low2", is_active=True)
    high = Product.objects.create(name="High2", is_active=True)
    ProductVariant.objects.create(
        product=low, size="M", color="Blue", sku="LOW2-M-BLU", price="10.00", stock=1, is_active=True
    )
    ProductVariant.objects.create(
        product=high, size="M", color="Blue", sku="HIGH2-M-BLU", price="20.00", stock=1, is_active=True
    )

    qs, sort = sort_products_queryset(request=request, queryset=Product.objects.all())

    assert sort == "price_desc"
    assert list(qs) == [high, low]


def test_sort_products_queryset_defaults_to_newest():
    rf = RequestFactory()
    request = rf.get("/shop/")
    older = Product.objects.create(name="Older", is_active=True)
    newer = Product.objects.create(name="Newer", is_active=True)

    qs, sort = sort_products_queryset(request=request, queryset=Product.objects.all())

    assert sort == ""
    assert list(qs) == [newer, older]


def test_sort_products_queryset_uses_cheapest_in_stock_price_first():
    rf = RequestFactory()
    request = rf.get("/shop/?sort=price_asc")
    product = Product.objects.create(name="Mixed Stock", is_active=True)
    cheaper_in_stock = Product.objects.create(name="Available", is_active=True)
    ProductVariant.objects.create(
        product=product,
        size="S",
        color="Black",
        sku="MIX-S-BLK",
        price="10.00",
        stock=0,
        is_active=True,
    )
    ProductVariant.objects.create(
        product=product,
        size="M",
        color="Black",
        sku="MIX-M-BLK",
        price="30.00",
        stock=2,
        is_active=True,
    )
    ProductVariant.objects.create(
        product=cheaper_in_stock,
        size="M",
        color="Black",
        sku="AVL-M-BLK",
        price="20.00",
        stock=1,
        is_active=True,
    )

    qs, sort = sort_products_queryset(request=request, queryset=Product.objects.all())

    assert sort == "price_asc"
    assert list(qs) == [cheaper_in_stock, product]
