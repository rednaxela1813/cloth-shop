import pytest
from django.db import IntegrityError

from apps.products.models import Category

pytestmark = pytest.mark.django_db


def test_category_generates_unique_slug_from_name():
    """
    Категория должна сама генерировать slug из name.
    Если slug уже занят — подобрать уникальный (суффикс -2, -3, ...).
    Это важно для стабильных URL каталога.
    """
    c1 = Category.objects.create(name="Shoes")
    c2 = Category.objects.create(name="Shoes")

    assert c1.slug == "shoes"
    assert c2.slug.startswith("shoes-")
    assert c1.slug != c2.slug


def test_category_has_public_uuid():
    """
    public_id — публичный UUID (будет нужен для API/внешних ссылок).
    """
    c = Category.objects.create(name="Men")
    assert c.public_id is not None


def test_cannot_delete_parent_category_if_has_children():
    """
    Дерево категорий нельзя ломать удалением родителя, у которого есть дети.
    Поэтому parent.on_delete=PROTECT.
    """
    parent = Category.objects.create(name="Men")
    Category.objects.create(name="Shoes", parent=parent)

    with pytest.raises(IntegrityError):
        parent.delete()
