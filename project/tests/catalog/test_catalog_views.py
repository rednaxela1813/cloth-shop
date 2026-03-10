import pytest
from django.urls import reverse

from apps.products.models import Category, Product, ProductCategory

pytestmark = pytest.mark.django_db


def test_catalog_list_shows_only_active_root_categories(client):
    """
    /catalog/ должен показывать только активные корневые категории (parent=None),
    отсортированные по sort_order, затем name.
    """
    root1 = Category.objects.create(name="Men", sort_order=2, is_active=True)
    root2 = Category.objects.create(name="Women", sort_order=1, is_active=True)

    # не корень
    Category.objects.create(name="Shoes", parent=root1, is_active=True)

    # неактивная
    Category.objects.create(name="Sale", sort_order=0, is_active=False)

    resp = client.get(reverse("catalog:list"))
    assert resp.status_code == 200

    cats = list(resp.context["categories"])
    assert cats == [root2, root1]


def test_catalog_category_detail_404_for_inactive_category(client):
    """
    Неактивная категория не должна открываться во витрине.
    """
    c = Category.objects.create(name="Sale", is_active=False)
    resp = client.get(reverse("catalog:category", kwargs={"slug": c.slug}))
    assert resp.status_code == 404


def test_catalog_category_detail_shows_only_active_products_in_category(client):
    """
    Страница категории должна показывать только активные товары,
    привязанные к этой категории.
    """
    cat = Category.objects.create(name="Shoes", is_active=True)

    active_p = Product.objects.create(name="Boots", brand="Gucci", price="10.00", is_active=True)
    inactive_p = Product.objects.create(name="Old Boots", brand="Gucci", price="5.00", is_active=False)

    ProductCategory.objects.create(product=active_p, category=cat, is_primary=True)
    ProductCategory.objects.create(product=inactive_p, category=cat, is_primary=True)

    resp = client.get(reverse("catalog:category", kwargs={"slug": cat.slug}))
    assert resp.status_code == 200

    products = list(resp.context["products"])
    assert products == [active_p]
