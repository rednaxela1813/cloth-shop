# project/apps/products/services/slug_service.py
from __future__ import annotations

from django.utils.text import slugify


def generate_unique_slug(*, model_cls, source_value: str, fallback: str = "item", base_limit: int = 200) -> str:
    """
    Генерирует уникальный slug для переданной модели.
    Алгоритм совместим с текущим поведением: base, base-2, base-3, ...
    """
    base = slugify(source_value)[:base_limit] or fallback
    slug = base
    index = 2

    while model_cls.objects.filter(slug=slug).exists():
        slug = f"{base}-{index}"
        index += 1

    return slug
