# project/apps/products/services/product_variant_presenter.py
from __future__ import annotations


def build_active_variants_payload(*, product):
    """
    Возвращает кортеж:
    1) активные варианты в стабильном порядке
    2) selected_variant (первый с stock > 0, иначе первый из списка, иначе None)
    3) payload для шаблона/JS
    """
    active_variants = list(product.variants.filter(is_active=True).order_by("color", "size", "id"))
    selected_variant = next((v for v in active_variants if v.stock > 0), active_variants[0] if active_variants else None)

    variant_payload = [
        {
            "public_id": str(v.public_id),
            "color": v.color,
            "size": v.size,
            "price": str(v.price),
            "compare_at": str(v.compare_at) if v.compare_at is not None else "",
            "stock": v.stock,
        }
        for v in active_variants
    ]
    return active_variants, selected_variant, variant_payload
