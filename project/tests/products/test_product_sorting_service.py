import pytest
from django.test import RequestFactory

from apps.products.models import Product
from apps.products.services.product_sorting_service import sort_products_queryset

pytestmark = pytest.mark.django_db


def test_sort_products_queryset_price_asc():
    rf = RequestFactory()
    request = rf.get("/shop/?sort=price_asc")
    low = Product.objects.create(name="Low", price="10.00", is_active=True)
    high = Product.objects.create(name="High", price="20.00", is_active=True)

    qs, sort = sort_products_queryset(request=request, queryset=Product.objects.all())

    assert sort == "price_asc"
    assert list(qs) == [low, high]


def test_sort_products_queryset_price_desc():
    rf = RequestFactory()
    request = rf.get("/shop/?sort=price_desc")
    low = Product.objects.create(name="Low2", price="10.00", is_active=True)
    high = Product.objects.create(name="High2", price="20.00", is_active=True)

    qs, sort = sort_products_queryset(request=request, queryset=Product.objects.all())

    assert sort == "price_desc"
    assert list(qs) == [high, low]


def test_sort_products_queryset_defaults_to_newest():
    rf = RequestFactory()
    request = rf.get("/shop/")
    older = Product.objects.create(name="Older", price="10.00", is_active=True)
    newer = Product.objects.create(name="Newer", price="20.00", is_active=True)

    qs, sort = sort_products_queryset(request=request, queryset=Product.objects.all())

    assert sort == ""
    assert list(qs) == [newer, older]
