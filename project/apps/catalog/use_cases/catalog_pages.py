from __future__ import annotations

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

from apps.catalog.breadcrumbs import breadcrumbs_for_catalog_index, breadcrumbs_for_category
from apps.products.models import Category, Product
from apps.products.services.product_sorting_service import sort_products_queryset


def build_catalog_index_context(*, request, page_size: int) -> dict:
    categories = Category.objects.roots()
    qs = Product.objects.filter(is_active=True)
    qs, sort = sort_products_queryset(request=request, queryset=qs)

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(request.GET.get("page") or 1)

    return {
        "categories": categories,
        "active_category": None,
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "products_count": paginator.count,
        "sort": sort,
        "breadcrumbs": breadcrumbs_for_catalog_index(),
    }


def build_catalog_category_context(*, request, slug: str, page_size: int) -> dict:
    categories = Category.objects.roots()
    active_category = get_object_or_404(Category, slug=slug, is_active=True)
    subcategories = active_category.children.filter(is_active=True).order_by("sort_order", "name", "id")

    qs = Product.objects.in_category(active_category)
    qs, sort = sort_products_queryset(request=request, queryset=qs)

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(request.GET.get("page") or 1)

    return {
        "categories": categories,
        "active_category": active_category,
        "category": active_category,
        "subcategories": subcategories,
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "products_count": paginator.count,
        "sort": sort,
        "breadcrumbs": breadcrumbs_for_category(active_category),
    }
