# project/apps/catalog/views.py
from django.shortcuts import render

from apps.catalog.use_cases import build_catalog_category_context, build_catalog_index_context

PAGE_SIZE = 12


def catalog_index_view(request):
    context = build_catalog_index_context(request=request, page_size=PAGE_SIZE)
    return render(request, "csm/pages/catalog.html", context)


def catalog_category_view(request, slug: str):
    context = build_catalog_category_context(request=request, slug=slug, page_size=PAGE_SIZE)
    return render(request, "catalog/category_detail.html", context)
