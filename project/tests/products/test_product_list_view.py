import pytest
from django.urls import reverse

from apps.products.models import Product, ProductVariant

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
    p_low = Product.objects.create(name="Low", brand="X", price="999.00", is_active=True)
    p_high = Product.objects.create(name="High", brand="X", price="1.00", is_active=True)
    ProductVariant.objects.create(product=p_low, size="M", color="Black", sku="LOW-M-BLK-LV", price="10.00", stock=2, is_active=True)
    ProductVariant.objects.create(product=p_high, size="M", color="Black", sku="HIGH-M-BLK-LV", price="20.00", stock=2, is_active=True)

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


def test_product_list_filter_by_brand(client):
    target = Product.objects.create(name="A", brand="Gucci", price="10.00", is_active=True)
    Product.objects.create(name="B", brand="Prada", price="10.00", is_active=True)

    resp = client.get(reverse("products:list"), {"brand": "Gucci"})

    assert resp.status_code == 200
    assert list(resp.context["page_obj"].object_list) == [target]


def test_product_list_filter_by_query_matches_name_or_brand(client):
    by_name = Product.objects.create(name="Leather Boots", brand="X", price="10.00", is_active=True)
    by_brand = Product.objects.create(name="Classic Coat", brand="Gucci", price="10.00", is_active=True)
    Product.objects.create(name="Sneakers", brand="Prada", price="10.00", is_active=True)

    by_name_resp = client.get(reverse("products:list"), {"q": "boots"})
    assert by_name_resp.status_code == 200
    assert list(by_name_resp.context["page_obj"].object_list) == [by_name]

    by_brand_resp = client.get(reverse("products:list"), {"q": "gucc"})
    assert by_brand_resp.status_code == 200
    assert list(by_brand_resp.context["page_obj"].object_list) == [by_brand]


def test_product_list_filter_by_price_range_uses_variant_display_price(client):
    in_range = Product.objects.create(name="In range", brand="X", price="999.00", is_active=True)
    out_of_range = Product.objects.create(name="Out range", brand="X", price="1.00", is_active=True)
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


def test_product_list_filter_in_stock_only(client):
    in_stock = Product.objects.create(name="Stock", brand="X", price="10.00", is_active=True)
    out_of_stock = Product.objects.create(name="No stock", brand="X", price="10.00", is_active=True)
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


def test_product_list_cards_link_to_product_detail_instead_of_posting_to_cart(client):
    product = Product.objects.create(name="Coat", brand="Gucci", price="10.00", is_active=True)
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
