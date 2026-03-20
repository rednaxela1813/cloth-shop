import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from apps.products.models import Product, ProductVariant

pytestmark = pytest.mark.django_db


def test_product_list_returns_page_obj_and_only_active(client):
    """
    /shop/ должен:
    - отдавать page_obj
    - включать только активные товары
    """
    p1 = Product.objects.create(name="A", brand="X", is_active=True)
    Product.objects.create(name="B", brand="X", is_active=False)

    resp = client.get(reverse("products:list"))
    assert resp.status_code == 200

    assert "page_obj" in resp.context
    page_obj = resp.context["page_obj"]
    assert list(page_obj.object_list) == [p1]


def test_product_list_sort_price_asc(client):
    """
    sort=price_asc сортирует по возрастанию цены.
    """
    p_low = Product.objects.create(name="Low", brand="X", is_active=True)
    p_high = Product.objects.create(name="High", brand="X", is_active=True)
    ProductVariant.objects.create(
        product=p_low, size="M", color="Black", sku="LOW-M-BLK-LV", price="10.00", stock=2, is_active=True
    )
    ProductVariant.objects.create(
        product=p_high, size="M", color="Black", sku="HIGH-M-BLK-LV", price="20.00", stock=2, is_active=True
    )

    resp = client.get(reverse("products:list") + "?sort=price_asc")
    page_obj = resp.context["page_obj"]
    assert list(page_obj.object_list) == [p_low, p_high]


def test_product_list_paginates(client):
    """
    Пагинация: если товаров больше чем page_size, page_obj должен резать список.
    """
    for i in range(13):
        Product.objects.create(name=f"P{i}", brand="X", is_active=True)

    resp = client.get(reverse("products:list"))
    page_obj = resp.context["page_obj"]

    assert page_obj.paginator.count == 13
    assert len(page_obj.object_list) == 12


def test_product_list_filter_by_brand(client):
    target = Product.objects.create(name="A", brand="Gucci", is_active=True)
    Product.objects.create(name="B", brand="Prada", is_active=True)

    resp = client.get(reverse("products:list"), {"brand": "Gucci"})

    assert resp.status_code == 200
    assert list(resp.context["page_obj"].object_list) == [target]


def test_product_list_filter_by_query_matches_name_or_brand(client):
    by_name = Product.objects.create(name="Leather Boots", brand="X", is_active=True)
    by_brand = Product.objects.create(name="Classic Coat", brand="Gucci", is_active=True)
    Product.objects.create(name="Sneakers", brand="Prada", is_active=True)

    by_name_resp = client.get(reverse("products:list"), {"q": "boots"})
    assert by_name_resp.status_code == 200
    assert list(by_name_resp.context["page_obj"].object_list) == [by_name]

    by_brand_resp = client.get(reverse("products:list"), {"q": "gucc"})
    assert by_brand_resp.status_code == 200
    assert list(by_brand_resp.context["page_obj"].object_list) == [by_brand]


def test_product_list_filter_by_price_range_uses_variant_display_price(client):
    in_range = Product.objects.create(name="In range", brand="X", is_active=True)
    out_of_range = Product.objects.create(name="Out range", brand="X", is_active=True)
    ProductVariant.objects.create(
        product=in_range,
        size="M",
        color="Black",
        sku="IN-M-BLK-LV",
        price="49.00",
        stock=1,
        is_active=True,
    )
    ProductVariant.objects.create(
        product=out_of_range,
        size="M",
        color="Black",
        sku="OUT-M-BLK-LV",
        price="120.00",
        stock=1,
        is_active=True,
    )

    resp = client.get(reverse("products:list"), {"min_price": "40", "max_price": "80"})

    assert resp.status_code == 200
    assert list(resp.context["page_obj"].object_list) == [in_range]


def test_product_list_price_filter_keeps_products_without_active_variant_price(client):
    missing_price = Product.objects.create(name="No Variant Price", brand="X", is_active=True)
    in_range = Product.objects.create(name="In range", brand="X", is_active=True)
    out_of_range = Product.objects.create(name="Out range", brand="X", is_active=True)
    ProductVariant.objects.create(
        product=in_range,
        size="M",
        color="Black",
        sku="IN2-M-BLK-LV",
        price="49.00",
        stock=1,
        is_active=True,
    )
    ProductVariant.objects.create(
        product=out_of_range,
        size="M",
        color="Black",
        sku="OUT2-M-BLK-LV",
        price="120.00",
        stock=1,
        is_active=True,
    )

    resp = client.get(reverse("products:list"), {"min_price": "40", "max_price": "80"})

    assert resp.status_code == 200
    assert list(resp.context["page_obj"].object_list) == [in_range, missing_price]


def test_product_list_filter_in_stock_only(client):
    in_stock = Product.objects.create(name="Stock", brand="X", is_active=True)
    out_of_stock = Product.objects.create(name="No stock", brand="X", is_active=True)
    ProductVariant.objects.create(
        product=in_stock,
        size="M",
        color="Black",
        sku="STOCK-M-BLK-LV",
        price="10.00",
        stock=3,
        is_active=True,
    )
    ProductVariant.objects.create(
        product=out_of_stock,
        size="M",
        color="Black",
        sku="NOSTOCK-M-BLK-LV",
        price="10.00",
        stock=0,
        is_active=True,
    )

    resp = client.get(reverse("products:list"), {"in_stock": "1"})

    assert resp.status_code == 200
    assert list(resp.context["page_obj"].object_list) == [in_stock]


def test_product_list_filter_new_only_uses_product_created_date(client):
    recent = Product.objects.create(name="Recent", brand="X", is_active=True)
    old = Product.objects.create(name="Old", brand="X", is_active=True)
    Product.objects.filter(pk=recent.pk).update(created=timezone.now() - timedelta(days=5))
    Product.objects.filter(pk=old.pk).update(created=timezone.now() - timedelta(days=20))

    resp = client.get(reverse("products:list"), {"new": "1"})

    assert resp.status_code == 200
    assert resp.context["new_only"] is True
    assert list(resp.context["page_obj"].object_list) == [Product.objects.get(pk=recent.pk)]


def test_product_list_cards_link_to_product_detail_instead_of_posting_to_cart(client):
    product = Product.objects.create(name="Coat", brand="Gucci", is_active=True)
    variant = ProductVariant.objects.create(
        product=product,
        size="M",
        color="Black",
        sku="COAT-M-BLK",
        price="10.00",
        stock=2,
        is_active=True,
    )

    resp = client.get(reverse("products:list"))

    assert resp.status_code == 200
    html = resp.content.decode("utf-8")
    assert reverse("products:detail", kwargs={"public_id": product.public_id, "slug": product.slug}) in html
    assert reverse("cart:add", kwargs={"public_id": variant.public_id}) not in html


def test_product_list_cards_link_to_product_detail_with_default_variant_query(client):
    product = Product.objects.create(name="Coat", brand="Gucci", is_active=True)
    variant = ProductVariant.objects.create(
        product=product,
        size="M",
        color="Black",
        sku="COAT-M-BLK-QS",
        price="10.00",
        stock=2,
        is_active=True,
    )

    resp = client.get(reverse("products:list"))

    assert resp.status_code == 200
    html = resp.content.decode("utf-8")
    expected_url = (
        reverse("products:detail", kwargs={"public_id": product.public_id, "slug": product.slug})
        + f"?variant={variant.public_id}"
    )
    assert expected_url in html
