# project/apps/products/services/product_sorting_service.py
from __future__ import annotations

from django.db.models import OuterRef, Subquery
from django.db.models.functions import Coalesce

from apps.products.models import ProductVariant


def with_sort_price(queryset):
    cheapest_in_stock_variant = (
        ProductVariant.objects
        .filter(
            product_id=OuterRef("pk"),
            is_active=True,
            stock__gt=0,
        )
        .order_by("price", "id")
        .values("price")[:1]
    )
    cheapest_variant = (
        ProductVariant.objects
        .filter(
            product_id=OuterRef("pk"),
            is_active=True,
        )
        .order_by("price", "id")
        .values("price")[:1]
    )

    return queryset.annotate(
        sort_price=Coalesce(
            Subquery(cheapest_in_stock_variant),
            Subquery(cheapest_variant),
        )
    )


def sort_products_queryset(*, request, queryset):
    sort = request.GET.get("sort") or ""

    if "sort_price" not in queryset.query.annotations:
        queryset = with_sort_price(queryset)

    if sort == "price_asc":
        queryset = queryset.order_by("sort_price", "id")
    elif sort == "price_desc":
        queryset = queryset.order_by("-sort_price", "id")
    else:
        queryset = queryset.order_by("-created", "id")

    return queryset, sort
