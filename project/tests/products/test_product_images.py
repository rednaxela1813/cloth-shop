# project/tests/products/test_product_images.py
import pytest

pytestmark = pytest.mark.django_db


def test_product_image_can_be_created_and_linked_to_product():
    from apps.products.models import Product, ProductImage

    p = Product.objects.create(name="Gucci Leather Bag")
    img = ProductImage.objects.create(
        product=p,
        alt="Front view",
        sort_order=10,
        # ничего не загружаем — это валидно для MVP
        # image_original/image_card/image_thumb могут быть пустыми
    )

    assert img.product_id == p.id
    assert img.alt == "Front view"
    assert str(img)  # не пустое


def test_product_images_related_name_and_ordering_by_sort_order_then_id():
    from apps.products.models import Product, ProductImage

    p = Product.objects.create(name="Prada Sunglasses")

    img2 = ProductImage.objects.create(product=p, sort_order=20, alt="2")
    img1 = ProductImage.objects.create(product=p, sort_order=10, alt="1")
    img3 = ProductImage.objects.create(product=p, sort_order=20, alt="3")

    images = list(p.images.all())  # related_name="images"

    assert images[0].id == img1.id
    # sort_order одинаковый, значит порядок по id
    assert images[1].id == img2.id
    assert images[2].id == img3.id


def test_product_primary_image_returns_primary_if_set_otherwise_first():
    from apps.products.models import Product, ProductImage

    p = Product.objects.create(name="Fendi Sneakers")

    # нет primary -> берем первую по сортировке (sort_order, id)
    a = ProductImage.objects.create(product=p, sort_order=20, is_primary=False, alt="A")
    b = ProductImage.objects.create(product=p, sort_order=10, is_primary=False, alt="B")

    assert p.primary_image.id == b.id  # ✅ property, НЕ вызываем как функцию

    # появляется primary -> берем его
    c = ProductImage.objects.create(product=p, sort_order=999, is_primary=True, alt="C")

    assert p.primary_image.id == c.id


def test_only_one_primary_image_per_product_is_enforced():
    """
    Если у товара уже есть primary, то при создании/сохранении второго primary
    старый должен стать is_primary=False.
    """
    from apps.products.models import Product, ProductImage

    p = Product.objects.create(name="D&G Dress")

    first = ProductImage.objects.create(product=p, is_primary=True, alt="First")
    second = ProductImage.objects.create(product=p, is_primary=True, alt="Second")

    first.refresh_from_db()
    second.refresh_from_db()

    assert first.is_primary is False
    assert second.is_primary is True
