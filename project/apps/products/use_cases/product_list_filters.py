from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.utils import timezone

from apps.products.models import Product

NEW_ARRIVALS_DAYS = 14


@dataclass(frozen=True)
class ProductListFiltersResult:
    # Отфильтрованный queryset, который уже можно отдавать в общий listing compose-layer.
    queryset: object
    # Дальше идут значения, нужные для повторного рендера sidebar/filter form.
    brands: object
    selected_brand: str
    selected_min_price: str
    selected_max_price: str
    in_stock_only: bool
    new_only: bool


def _read_decimal(raw_value: str) -> Decimal | None:
    # Query params приходят строками и могут быть пустыми/невалидными.
    # Нормализуем их здесь, чтобы page use-case не дублировал эту защиту.
    value = (raw_value or "").strip()
    if not value:
        return None
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError):
        return None
    if parsed < 0:
        return None
    return parsed


def apply_product_list_filters(*, request, queryset) -> ProductListFiltersResult:
    # Это shop-specific фильтрация для /shop/.
    # Helper знает, какие query params поддерживает storefront,
    # и возвращает не только queryset, но и UI state для повторного рендера формы.
    filtered_queryset = queryset

    query = (request.GET.get("q") or "").strip()
    if query:
        filtered_queryset = filtered_queryset.filter(
            Q(name__icontains=query) | Q(brand__icontains=query)
        )

    selected_brand = (request.GET.get("brand") or "").strip()
    if selected_brand:
        filtered_queryset = filtered_queryset.filter(brand__iexact=selected_brand)

    selected_min_price = request.GET.get("min_price", "")
    selected_max_price = request.GET.get("max_price", "")
    min_price = _read_decimal(selected_min_price)
    max_price = _read_decimal(selected_max_price)
    if min_price is not None or max_price is not None:
        # sort_price уже должен быть подготовлен до вызова helper'а.
        # Мы специально не знаем здесь, как именно он был аннотирован,
        # только используем согласованный контракт поля.
        price_filters = Q(sort_price__isnull=True)
        if min_price is not None and max_price is not None:
            price_filters |= Q(sort_price__gte=min_price, sort_price__lte=max_price)
        elif min_price is not None:
            price_filters |= Q(sort_price__gte=min_price)
        else:
            price_filters |= Q(sort_price__lte=max_price)
        filtered_queryset = filtered_queryset.filter(price_filters)

    in_stock_only = request.GET.get("in_stock") == "1"
    if in_stock_only:
        filtered_queryset = filtered_queryset.filter(
            variants__is_active=True,
            variants__stock__gt=0,
        ).distinct()

    new_only = request.GET.get("new") == "1"
    if new_only:
        cutoff = timezone.now() - timedelta(days=NEW_ARRIVALS_DAYS)
        filtered_queryset = filtered_queryset.filter(created__gte=cutoff)

    # Бренды для sidebar считаются отдельно от текущего queryset:
    # это поведение уже было в проекте, и мы его сохраняем без изменений.
    brands = (
        Product.objects.filter(is_active=True)
        .exclude(brand="")
        .values_list("brand", flat=True)
        .distinct()
        .order_by("brand")
    )

    return ProductListFiltersResult(
        queryset=filtered_queryset,
        brands=brands,
        selected_brand=selected_brand,
        selected_min_price=selected_min_price,
        selected_max_price=selected_max_price,
        in_stock_only=in_stock_only,
        new_only=new_only,
    )
