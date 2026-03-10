import pytest
from django.urls import reverse

from apps.products.models import Product

pytestmark = pytest.mark.django_db


def test_product_list_returns_page_obj_and_only_active(client):
    """
    /shop/ должен:
    - отдавать page_obj
    - включать только активные товары
    """
    p1 = Product.objects.create(name="A", brand="X", price="10.00", is_active=True)
    Product.objects.create(name="B", brand="X", price="20.00", is_active=False)

    resp = client.get(reverse("products:list"))
    assert resp.status_code == 200

    assert "page_obj" in resp.context
    page_obj = resp.context["page_obj"]
    assert list(page_obj.object_list) == [p1]


def test_product_list_sort_price_asc(client):
    """
    sort=price_asc сортирует по возрастанию цены.
    """
    p_low = Product.objects.create(name="Low", brand="X", price="10.00", is_active=True)
    p_high = Product.objects.create(name="High", brand="X", price="20.00", is_active=True)

    resp = client.get(reverse("products:list") + "?sort=price_asc")
    page_obj = resp.context["page_obj"]
    assert list(page_obj.object_list) == [p_low, p_high]


def test_product_list_paginates(client):
    """
    Пагинация: если товаров больше чем page_size, page_obj должен резать список.
    """
    for i in range(13):
        Product.objects.create(name=f"P{i}", brand="X", price="10.00", is_active=True)

    resp = client.get(reverse("products:list"))
    page_obj = resp.context["page_obj"]

    assert page_obj.paginator.count == 13
    assert len(page_obj.object_list) == 12
