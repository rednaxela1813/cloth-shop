import pytest
from django.urls import reverse

from apps.products.models import Category, Product, ProductCategory

pytestmark = pytest.mark.django_db


def test_catalog_200(client):
    resp = client.get(reverse("catalog:list"))
    assert resp.status_code == 200


def test_catalog_category_filters_products(client):
    cat = Category.objects.create(name="Shoes", is_active=True)

    p1 = Product.objects.create(name="Boots", brand="Gucci", price="10.00", is_active=True)
    p2 = Product.objects.create(name="Bag", brand="Prada", price="20.00", is_active=True)

    ProductCategory.objects.create(product=p1, category=cat, is_primary=True)

    resp = client.get(reverse("catalog:category", kwargs={"slug": cat.slug}))
    assert resp.status_code == 200

    html = resp.content.decode("utf-8")
    assert "Boots" in html
    assert "Bag" not in html


def test_catalog_category_404_for_inactive_category(client):
    cat = Category.objects.create(name="Hidden", is_active=False)

    resp = client.get(reverse("catalog:category", kwargs={"slug": cat.slug}))
    assert resp.status_code == 404
