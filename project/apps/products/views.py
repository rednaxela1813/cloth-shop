#project/apps/products/views.py
from django.shortcuts import render, redirect

from apps.products.use_cases import build_product_detail_result, build_product_list_context


PAGE_SIZE = 12


def product_list_view(request):
    context = build_product_list_context(request=request, page_size=PAGE_SIZE)
    return render(request, "csm/pages/product_list.html", context)





def product_detail_view(request, public_id, slug):
    result = build_product_detail_result(request=request, public_id=public_id, slug=slug)
    if result.redirect_slug:
        return redirect(
            "products:detail",
            public_id=result.product.public_id,
            slug=result.redirect_slug,
            permanent=True,
        )
    return render(request, "csm/pages/product_detail.html", result.context)
