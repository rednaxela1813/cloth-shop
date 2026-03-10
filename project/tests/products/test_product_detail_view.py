import pytest
from django.urls import reverse

from apps.products.models import Product, ProductImage, ProductVariant

pytestmark = pytest.mark.django_db


def test_product_detail_200_for_active_product(client):
    """
    Активный товар открывается по slug.
    Контекст должен содержать product, images, primary_image.
    """
    p = Product.objects.create(
        name="Boots",
        brand="Gucci",
        price="10.00",
        is_active=True,
    )

    # без реального файла — просто проверяем, что queryset/контекст работает
    ProductImage.objects.create(product=p, alt="one", sort_order=2, is_primary=False)
    ProductImage.objects.create(product=p, alt="main", sort_order=1, is_primary=True)

    resp = client.get(reverse("products:detail", kwargs={"public_id": p.public_id, "slug": p.slug}))
    assert resp.status_code == 200

    assert resp.context["product"].id == p.id

    images = list(resp.context["images"])
    assert len(images) == 2

    primary = resp.context["primary_image"]
    assert primary is not None
    assert primary.is_primary is True


def test_product_detail_404_for_inactive_product(client):
    """
    Неактивный товар не должен открываться во витрине.
    """
    p = Product.objects.create(
        name="Hidden Boots",
        brand="Gucci",
        price="10.00",
        is_active=False,
    )
    resp = client.get(reverse("products:detail", kwargs={"public_id": p.public_id, "slug": p.slug}))
    assert resp.status_code == 404










def test_product_detail_200_for_active_product(client):
    """
    Активный товар открывается.
    В контексте должны быть:
    - product
    - images
    - primary_image
    - related_products
    """
    product = Product.objects.create(
        name="Boots",
        brand="Gucci",
        price="120.00",
        is_active=True,
    )

    # изображения
    img1 = ProductImage.objects.create(
        product=product,
        alt="secondary",
        sort_order=2,
        is_primary=False,
    )
    img2 = ProductImage.objects.create(
        product=product,
        alt="primary",
        sort_order=1,
        is_primary=True,
    )

    url = reverse(
        "products:detail",
        kwargs={"public_id": product.public_id, "slug": product.slug},
    )
    response = client.get(url)

    assert response.status_code == 200

    ctx = response.context
    assert ctx["product"].id == product.id
    assert list(ctx["images"]) == [img2, img1]
    assert ctx["primary_image"].id == img2.id
    assert ctx["related_products"].count() == 0


def test_product_detail_404_for_inactive_product(client):
    """
    Неактивный товар не должен открываться.
    """
    product = Product.objects.create(
        name="Hidden",
        brand="Gucci",
        price="99.00",
        is_active=False,
    )

    url = reverse(
        "products:detail",
        kwargs={"public_id": product.public_id, "slug": product.slug},
    )
    response = client.get(url)

    assert response.status_code == 404


def test_product_detail_primary_image_fallback_to_first_by_sort_order(client):
    """
    Если is_primary нет — берётся первый по sort_order.
    """
    product = Product.objects.create(
        name="Bag",
        brand="Prada",
        price="300.00",
        is_active=True,
    )

    img1 = ProductImage.objects.create(
        product=product,
        alt="img1",
        sort_order=5,
        is_primary=False,
    )
    img2 = ProductImage.objects.create(
        product=product,
        alt="img2",
        sort_order=1,
        is_primary=False,
    )

    url = reverse(
        "products:detail",
        kwargs={"public_id": product.public_id, "slug": product.slug},
    )
    response = client.get(url)

    ctx = response.context
    assert ctx["primary_image"].id == img2.id


def test_product_detail_related_products_same_brand_only(client):
    """
    Related products:
    - активные
    - тот же бренд
    - без текущего товара
    """
    main = Product.objects.create(
        name="Main",
        brand="Dolce",
        price="200.00",
        is_active=True,
    )

    related = Product.objects.create(
        name="Related",
        brand="Dolce",
        price="180.00",
        is_active=True,
    )

    other_brand = Product.objects.create(
        name="Other",
        brand="Armani",
        price="180.00",
        is_active=True,
    )

    inactive = Product.objects.create(
        name="Inactive",
        brand="Dolce",
        price="150.00",
        is_active=False,
    )

    url = reverse(
        "products:detail",
        kwargs={"public_id": main.public_id, "slug": main.slug},
    )
    response = client.get(url)

    related_products = response.context["related_products"]

    assert related in related_products
    assert other_brand not in related_products
    assert inactive not in related_products
    assert main not in related_products


def test_product_detail_redirects_on_wrong_slug(client):
    product = Product.objects.create(
        name="Silk Dress",
        brand="Gucci",
        price="220.00",
        is_active=True,
    )

    wrong_url = reverse(
        "products:detail",
        kwargs={"public_id": product.public_id, "slug": "wrong-slug"},
    )
    response = client.get(wrong_url)

    assert response.status_code == 301
    assert response["Location"].endswith(
        reverse("products:detail", kwargs={"public_id": product.public_id, "slug": product.slug})
    )


def test_product_detail_exposes_variant_selection_context(client):
    product = Product.objects.create(
        name="Variant Dress",
        brand="Gucci",
        price="220.00",
        is_active=True,
    )
    v1 = ProductVariant.objects.create(
        product=product,
        size="S",
        color="Black",
        sku="VD-BLK-S",
        price="220.00",
        stock=0,
        is_active=True,
    )
    v2 = ProductVariant.objects.create(
        product=product,
        size="M",
        color="Black",
        sku="VD-BLK-M",
        price="230.00",
        stock=3,
        is_active=True,
    )

    response = client.get(
        reverse("products:detail", kwargs={"public_id": product.public_id, "slug": product.slug})
    )

    assert response.status_code == 200
    assert response.context["selected_variant"].id == v2.id
    payload = response.context["variant_payload"]
    assert len(payload) == 2
