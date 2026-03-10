from __future__ import annotations

from django.db.models import F, Min, Q
from django.db.models.functions import Coalesce


def with_sort_price(queryset):
    return queryset.annotate(
        sort_price=Coalesce(
            Min("variants__price", filter=Q(variants__is_active=True)),
            F("price"),
        )
    )


def sort_products_queryset(*, request, queryset):
    """
    Единый контракт сортировки для витринных списков товаров.
    Возвращает (queryset, sort_key), чтобы UI мог отобразить выбранный режим.
    """
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
