import pytest

pytestmark = pytest.mark.django_db


def test_enforce_single_primary_product_category_unsets_previous_primary():
    from apps.products.models import Category, Product, ProductCategory
    from apps.products.services.product_category_service import enforce_single_primary_product_category

    product = Product.objects.create(name="Bag")
    cat_a = Category.objects.create(name="Men")
    cat_b = Category.objects.create(name="Accessories")

    old_primary = ProductCategory.objects.create(product=product, category=cat_a, is_primary=True)
    new_primary = ProductCategory.objects.create(product=product, category=cat_b, is_primary=True)

    # Проверяем сервис напрямую, чтобы тестировать слой доменной политики отдельно от ORM-хука.
    enforce_single_primary_product_category(new_primary)

    old_primary.refresh_from_db()
    new_primary.refresh_from_db()

    assert old_primary.is_primary is False
    assert new_primary.is_primary is True


def test_enforce_single_primary_product_category_noop_for_non_primary():
    from apps.products.models import Category, Product, ProductCategory
    from apps.products.services.product_category_service import enforce_single_primary_product_category

    product = Product.objects.create(name="Hat")
    cat_a = Category.objects.create(name="Women")
    cat_b = Category.objects.create(name="Sale")

    primary_link = ProductCategory.objects.create(product=product, category=cat_a, is_primary=True)
    non_primary_link = ProductCategory.objects.create(product=product, category=cat_b, is_primary=False)

    enforce_single_primary_product_category(non_primary_link)

    primary_link.refresh_from_db()
    non_primary_link.refresh_from_db()

    assert primary_link.is_primary is True
    assert non_primary_link.is_primary is False
