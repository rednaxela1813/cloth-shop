import pytest
from apps.products.models import Category, Product, ProductCategory

pytestmark = pytest.mark.django_db


def test_product_queryset_in_category_returns_only_active_products_sorted():
    """
    in_category() должен вернуть только активные товары категории
    в сортировке -created (как сейчас в view).
    """
    cat = Category.objects.create(name="Shoes", is_active=True)

    p_old = Product.objects.create(name="Old", brand="X", is_active=True)
    p_new = Product.objects.create(name="New", brand="X", is_active=True)
    p_inactive = Product.objects.create(name="Inactive", brand="X", is_active=False)

    ProductCategory.objects.create(product=p_old, category=cat)
    ProductCategory.objects.create(product=p_new, category=cat)
    ProductCategory.objects.create(product=p_inactive, category=cat)

    assert list(Product.objects.in_category(cat)) == [p_new, p_old]
