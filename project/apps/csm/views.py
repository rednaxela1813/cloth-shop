# project/apps/csm/views.py
from django.conf import settings
from django.db.models import Prefetch
from django.shortcuts import render

from apps.products.models import Product, ProductImage, ProductVariant
from .forms import ContactMessageForm


def _random_category_cover_url(*, category_slug: str) -> str:
    image = (
        ProductImage.objects.filter(
            product__is_active=True,
            product__categories__slug=category_slug,
            product__categories__is_active=True,
        )
        .distinct()
        .order_by("?")
        .first()
    )
    if not image:
        return ""
    if image.image_card:
        return image.image_card.url
    if image.image_thumb:
        return image.image_thumb.url
    if image.image_original:
        return image.image_original.url
    return image.image_url or ""


def home_view(request):
    trending_products = (
        Product.objects.trending()
        .prefetch_related(
            Prefetch(
                "variants",
                queryset=ProductVariant.objects.filter(is_active=True).order_by("price", "id"),
                to_attr="_prefetched_active_variants_for_pricing",
            )
        )[:8]
    )

    context = {
        "title": "Italian Luxury Clothing",
        "meta_description": "Nakupujte taliansku módu online – luxusné značky, rýchle doručenie.",
        "cart_count": 0,
        "trending_products": trending_products,
        "women_tile_image_url": _random_category_cover_url(category_slug="women"),
        "men_tile_image_url": _random_category_cover_url(category_slug="men"),
        "sale_tile_image_url": _random_category_cover_url(category_slug="sale"),
    }
    return render(request, "csm/pages/home.html", context)


def help_view(request):
    context = {
        "title": "Help - Italian Luxury Clothing",
        "meta_description": "Get help with your orders, shipping, returns, and more at Italian Luxury Clothing.",
        "cart_count": 0,
    }
    return render(request, "csm/pages/help.html", context)


def returns_view(request):
    context = {
        "title": "Returns - Italian Luxury Clothing",
        "meta_description": "Learn about our return policy and how to return items at Italian Luxury Clothing.",
        "cart_count": 0,
    }
    return render(request, "csm/pages/returns.html", context)


def contact_view(request):
    form_submitted = False

    if request.method == "POST":
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            form_submitted = True
            form = ContactMessageForm()

            if getattr(settings, "CONTACT_SEND_ENABLED", False):
                # Placeholder for future integrations (email/messenger).
                pass
    else:
        form = ContactMessageForm()

    context = {
        "title": "Kontakt - Ricotti",
        "meta_description": "Kontaktujte Ricotti. Odpovieme na vaše otázky o produktoch a objednávkach.",
        "cart_count": 0,
        "form": form,
        "form_submitted": form_submitted,
    }
    return render(request, "csm/pages/contact.html", context)
