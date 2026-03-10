import pytest

from apps.products.models import Category, Product, ProductCategory

pytestmark = pytest.mark.django_db


def test_product_can_have_multiple_categories():
    """
    Товар может быть привязан к нескольким категориям.
    """
    p = Product.objects.create(name="Boots", brand="Gucci", price="10.00", is_active=True)

    c1 = Category.objects.create(name="Men")
    c2 = Category.objects.create(name="Shoes")

    ProductCategory.objects.create(product=p, category=c1)
    ProductCategory.objects.create(product=p, category=c2)

    assert p.categories.count() == 2


def test_only_one_primary_category_per_product():
    """
    Для SEO нужна "основная" категория товара (canonical URL, breadcrumbs).
    Гарантируем: у одного товара может быть только одна primary category.
    Если создаём/сохраняем новую primary — старая должна сброситься.
    """
    p = Product.objects.create(name="Boots", brand="Gucci", price="10.00", is_active=True)

    c1 = Category.objects.create(name="Men")
    c2 = Category.objects.create(name="Shoes")

    link1 = ProductCategory.objects.create(product=p, category=c1, is_primary=True)
    link2 = ProductCategory.objects.create(product=p, category=c2, is_primary=True)

    link1.refresh_from_db()
    link2.refresh_from_db()

    assert link2.is_primary is True
    assert link1.is_primary is False
