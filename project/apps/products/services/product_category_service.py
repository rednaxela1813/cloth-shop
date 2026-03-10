from __future__ import annotations


def enforce_single_primary_product_category(product_category) -> None:
    """
    Гарантирует единственную primary-категорию для товара.
    Вызывается после save(), когда можно корректно исключить текущую запись по id.
    """
    if not product_category.is_primary:
        return

    product_category.__class__.objects.filter(
        product=product_category.product,
        is_primary=True,
    ).exclude(id=product_category.id).update(is_primary=False)
