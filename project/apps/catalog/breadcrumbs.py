# apps/catalog/breadcrumbs.py
from __future__ import annotations

from typing import List, Dict
from django.urls import reverse

from apps.products.models import Category, Product

Breadcrumb = Dict[str, str]


def breadcrumbs_for_catalog_index() -> List[Breadcrumb]:
    return [
        {"title": "Home", "url": reverse("home")},
        {"title": "Catalog", "url": reverse("catalog:list")},
    ]


def breadcrumbs_for_category(category: Category) -> List[Breadcrumb]:
    return [
        {"title": "Home", "url": reverse("home")},
        {"title": "Catalog", "url": reverse("catalog:list")},
        {"title": category.name, "url": reverse("catalog:category", kwargs={"slug": category.slug})},
    ]


def breadcrumbs_for_product(product: Product) -> List[Breadcrumb]:
    """
    Home -> Catalog -> (Category?) -> Product
    """
    items: List[Breadcrumb] = [
        {"title": "Home", "url": reverse("home")},
        {"title": "Catalog", "url": reverse("catalog:list")},
    ]

    cat = product.primary_category
    if cat:
        items.append(
            {"title": cat.name, "url": reverse("catalog:category", kwargs={"slug": cat.slug})}
        )

    items.append(
        {
            "title": product.name,
            "url": reverse(
                "products:detail",
                kwargs={"public_id": product.public_id, "slug": product.slug},
            ),
        }
    )
    return items
