import pytest
from django.http import Http404
from django.test import RequestFactory

from apps.catalog.use_cases.catalog_pages import build_catalog_category_context, build_catalog_index_context
from apps.products.models import Category, Product, ProductCategory, ProductVariant

pytestmark = pytest.mark.django_db


def test_build_catalog_index_context_applies_sort_and_pagination():
    rf = RequestFactory()
    request = rf.get("/catalog/?sort=price_asc&page=1")

    low = Product.objects.create(name="Low", price="999.00", is_active=True)
    high = Product.objects.create(name="High", price="1.00", is_active=True)
    Product.objects.create(name="Hidden", price="1.00", is_active=False)
    ProductVariant.objects.create(product=low, size="L", color="Black", sku="CAT-LOW-L-BLK", price="10.00", stock=1, is_active=True)
    ProductVariant.objects.create(product=high, size="L", color="Black", sku="CAT-HIGH-L-BLK", price="20.00", stock=1, is_active=True)

    context = build_catalog_index_context(request=request, page_size=12)

    assert context["sort"] == "price_asc"
    assert context["products_count"] == 2
    assert list(context["products"]) == [low, high]


def test_build_catalog_category_context_returns_active_category_products_and_subcategories():
    rf = RequestFactory()
    parent = Category.objects.create(name="Shoes", is_active=True)
    active_child = Category.objects.create(name="Boots", parent=parent, is_active=True)
    Category.objects.create(name="Archive", parent=parent, is_active=False)

    active_product = Product.objects.create(name="Boot A", price="10.00", is_active=True)
    inactive_product = Product.objects.create(name="Boot B", price="20.00", is_active=False)
    child_product = Product.objects.create(name="Boot Child", price="15.00", is_active=True)
    ProductCategory.objects.create(product=active_product, category=parent, is_primary=True)
    ProductCategory.objects.create(product=inactive_product, category=parent, is_primary=True)
    ProductCategory.objects.create(product=child_product, category=active_child, is_primary=True)

    request = rf.get(f"/catalog/{parent.slug}/")
    context = build_catalog_category_context(request=request, slug=parent.slug, page_size=12)

    assert context["active_category"].id == parent.id
    assert list(context["subcategories"]) == [active_child]
    assert list(context["products"]) == [active_product]


def test_build_catalog_category_context_raises_404_for_inactive_category():
    rf = RequestFactory()
    inactive = Category.objects.create(name="Sale", is_active=False)
    request = rf.get(f"/catalog/{inactive.slug}/")

    with pytest.raises(Http404):
        build_catalog_category_context(request=request, slug=inactive.slug, page_size=12)
