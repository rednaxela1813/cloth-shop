import pytest
from django.urls import reverse

from apps.products.models import Category, Product, ProductCategory

pytestmark = pytest.mark.django_db


def test_catalog_index_has_breadcrumbs(client):
    """
    /catalog/ должен показывать breadcrumbs: Home -> Catalog
    """
    url = reverse("catalog:list")
    resp = client.get(url)
    assert resp.status_code == 200

    breadcrumbs = resp.context["breadcrumbs"]
    assert breadcrumbs[0]["title"] == "Home"
    assert breadcrumbs[1]["title"] == "Catalog"
    assert breadcrumbs[1]["url"] == url


def test_catalog_category_has_breadcrumbs(client):
    """
    /catalog/<slug>/ должен показывать: Home -> Catalog -> Category
    """
    cat = Category.objects.create(name="Shoes", is_active=True)
    product = Product.objects.create(name="Derby", brand="Test", price="10.00", is_active=True)
    ProductCategory.objects.create(product=product, category=cat, is_primary=True)
    url = reverse("catalog:category", kwargs={"slug": cat.slug})
    resp = client.get(url)
    assert resp.status_code == 200

    breadcrumbs = resp.context["breadcrumbs"]
    assert [b["title"] for b in breadcrumbs] == ["Home", "Catalog", "Shoes"]
    assert breadcrumbs[-1]["url"] == url


def test_product_detail_breadcrumbs_use_primary_category(client):
    """
    На product detail breadcrumbs должны включать primary category, если она есть.
    """
    cat1 = Category.objects.create(name="Shoes", is_active=True, sort_order=10)
    cat2 = Category.objects.create(name="Bags", is_active=True, sort_order=1)

    p = Product.objects.create(name="Boots", brand="Gucci", price="10.00", is_active=True)

    # Привяжем обе категории, но primary сделаем cat1 (Shoes)
    ProductCategory.objects.create(product=p, category=cat2, sort_order=1, is_primary=False)
    ProductCategory.objects.create(product=p, category=cat1, sort_order=10, is_primary=True)

    url = reverse("products:detail", kwargs={"public_id": p.public_id, "slug": p.slug})
    resp = client.get(url)
    assert resp.status_code == 200

    breadcrumbs = resp.context["breadcrumbs"]
    titles = [b["title"] for b in breadcrumbs]
    assert titles == ["Home", "Catalog", "Shoes", "Boots"]


def test_product_detail_breadcrumbs_fallback_to_first_category(client):
    """
    Если primary category нет — берём первую по sort_order/id.
    """
    cat1 = Category.objects.create(name="Shoes", is_active=True, sort_order=10)
    cat2 = Category.objects.create(name="Bags", is_active=True, sort_order=1)

    p = Product.objects.create(name="Boots", brand="Gucci", price="10.00", is_active=True)

    # primary нигде не ставим
    ProductCategory.objects.create(product=p, category=cat1, sort_order=10, is_primary=False)
    ProductCategory.objects.create(product=p, category=cat2, sort_order=1, is_primary=False)

    url = reverse("products:detail", kwargs={"public_id": p.public_id, "slug": p.slug})
    resp = client.get(url)
    assert resp.status_code == 200

    breadcrumbs = resp.context["breadcrumbs"]
    titles = [b["title"] for b in breadcrumbs]

    # так как sort_order у Bags меньше, она попадёт в breadcrumbs
    assert titles == ["Home", "Catalog", "Bags", "Boots"]
