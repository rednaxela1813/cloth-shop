from __future__ import annotations

from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404

from apps.catalog.breadcrumbs import breadcrumbs_for_catalog_index, breadcrumbs_for_category
from apps.products.models import Category, Product, ProductVariant
from apps.products.services.product_sorting_service import sort_products_queryset


def build_catalog_index_context(*, request, page_size: int) -> dict:
    categories = Category.objects.roots()
    qs = Product.objects.filter(is_active=True).prefetch_related(
        Prefetch(
            "variants",
            queryset=ProductVariant.objects.filter(is_active=True).order_by("price", "id"),
            to_attr="_prefetched_active_variants_for_pricing",
        )
    )
    qs, sort = sort_products_queryset(request=request, queryset=qs)

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(request.GET.get("page") or 1)
    query_params = request.GET.copy()
    query_params.pop("page", None)

    return {
        "categories": categories,
        "active_category": None,
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "products_count": paginator.count,
        "sort": sort,
        "breadcrumbs": breadcrumbs_for_catalog_index(),
        "pagination_query": query_params.urlencode(),
    }


def build_catalog_category_context(*, request, slug: str, page_size: int) -> dict:
    categories = Category.objects.roots().filter(products__is_active=True).distinct()
    active_category = get_object_or_404(Category, slug=slug, is_active=True)
    if not active_category.products.filter(is_active=True).exists():
        raise Http404("Category has no active products.")

    subcategories = (
        active_category.children.filter(is_active=True, products__is_active=True)
        .distinct()
        .order_by("sort_order", "name", "id")
    )
    selected_root_category = active_category.parent if active_category.parent_id else active_category
    sidebar_subcategories = (
        selected_root_category.children.filter(is_active=True, products__is_active=True)
        .distinct()
        .order_by("sort_order", "name", "id")
    )

    qs = Product.objects.in_category(active_category).prefetch_related(
        Prefetch(
            "variants",
            queryset=ProductVariant.objects.filter(is_active=True).order_by("price", "id"),
            to_attr="_prefetched_active_variants_for_pricing",
        )
    )
    qs, sort = sort_products_queryset(request=request, queryset=qs)

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(request.GET.get("page") or 1)
    query_params = request.GET.copy()
    query_params.pop("page", None)

    return {
        "categories": categories,
        "active_category": active_category,
        "category": active_category,
        "subcategories": subcategories,
        "selected_root_category": selected_root_category,
        "sidebar_subcategories": sidebar_subcategories,
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "products_count": paginator.count,
        "sort": sort,
        "breadcrumbs": breadcrumbs_for_category(active_category),
        "pagination_query": query_params.urlencode(),
    }
