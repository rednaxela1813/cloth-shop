from __future__ import annotations


def sort_products_queryset(*, request, queryset):
    """
    Единый контракт сортировки для витринных списков товаров.
    Возвращает (queryset, sort_key), чтобы UI мог отобразить выбранный режим.
    """
    sort = request.GET.get("sort") or ""
    if sort == "price_asc":
        queryset = queryset.order_by("price", "id")
    elif sort == "price_desc":
        queryset = queryset.order_by("-price", "id")
    else:
        queryset = queryset.order_by("-created", "id")
    return queryset, sort
