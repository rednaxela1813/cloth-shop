import pytest
from apps.products.models import Category

pytestmark = pytest.mark.django_db


def test_category_queryset_roots_returns_only_active_roots_sorted():
    """
    roots() должен вернуть только активные корневые категории
    в сортировке sort_order, name.
    """
    root1 = Category.objects.create(name="Men", sort_order=2, is_active=True)
    root2 = Category.objects.create(name="Women", sort_order=1, is_active=True)
    Category.objects.create(name="Shoes", parent=root1, is_active=True)
    Category.objects.create(name="Sale", is_active=False, sort_order=0)

    assert list(Category.objects.roots()) == [root2, root1]
