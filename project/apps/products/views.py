#project/apps/products/views.py
from django.shortcuts import render, redirect
from django.utils.http import urlencode

from apps.products.use_cases import build_product_detail_result, build_product_list_context


PAGE_SIZE = 12


def product_list_view(request):
    context = build_product_list_context(request=request, page_size=PAGE_SIZE)
    return render(request, "csm/pages/product_list.html", context)





def product_detail_view(request, public_id, slug):
    result = build_product_detail_result(request=request, public_id=public_id, slug=slug)
    if result.redirect_slug:
        response = redirect(
            "products:detail",
            public_id=result.product.public_id,
            slug=result.redirect_slug,
            permanent=True,
        )
        variant_public_id = (request.GET.get("variant") or "").strip()
        if variant_public_id:
            response["Location"] = f"{response['Location']}?{urlencode({'variant': variant_public_id})}"
        return response
    return render(request, "csm/pages/product_detail.html", result.context)
