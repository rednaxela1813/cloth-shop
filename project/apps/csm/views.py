# project/apps/csm/views.py
from datetime import timedelta

from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from apps.csm.models import HomeHeroContent
from apps.customer_comm.application.use_cases import submit_inquiry
from apps.customer_comm.presentation.forms import PublicInquiryForm
from apps.products.models import Category, Product
from apps.products.services.listing_service import with_product_card_related
from apps.products.services.product_card_presenter import build_product_card_payload
from apps.shipping.services import get_return_window_days

NEW_ARRIVALS_DAYS = 14


def healthz_view(request):
    return HttpResponse("ok", content_type="text/plain")


def _category_cover_urls(*, slugs: tuple[str, ...]) -> dict[str, str]:
    categories = Category.objects.active().filter(slug__in=slugs)
    return {category.slug: category.resolved_cover_image_url for category in categories}


def _home_hero_content() -> HomeHeroContent:
    hero_content = HomeHeroContent.objects.first()
    if hero_content is not None:
        return hero_content
    return HomeHeroContent()


def home_view(request):
    hero_content = _home_hero_content()
    categories = Category.objects.roots()
    category_cover_urls = _category_cover_urls(slugs=("women", "men", "sale"))
    new_arrivals_cutoff = timezone.now() - timedelta(days=NEW_ARRIVALS_DAYS)
    has_new_arrivals = Product.objects.active().filter(created__gte=new_arrivals_cutoff).exists()

    selected_category_slug = (request.GET.get("category") or "").strip()
    selected_subcategory_slug = (request.GET.get("subcategory") or "").strip()

    selected_category = categories.filter(slug=selected_category_slug).first() if selected_category_slug else None
    subcategories = (
        Category.objects.active()
        .filter(parent=selected_category)
        .order_by("sort_order", "name", "id")
        if selected_category
        else Category.objects.none()
    )

    selected_subcategory = (
        subcategories.filter(slug=selected_subcategory_slug).first() if selected_subcategory_slug else None
    )

    trending_qs = Product.objects.trending()
    if selected_subcategory:
        trending_qs = trending_qs.filter(categories=selected_subcategory)
    elif selected_category:
        trending_qs = trending_qs.filter(categories=selected_category)

    trending_products = with_product_card_related(trending_qs.distinct())[:8]
    trending_product_cards = [
        build_product_card_payload(product=product, request=request, cta_mode="details")
        for product in trending_products
    ]

    context = {
        "title": "Italian Luxury Clothing",
        "meta_description": "Nakupujte taliansku módu online – luxusné značky, rýchle doručenie.",
        "cart_count": 0,
        "categories": categories,
        "subcategories": subcategories,
        "selected_category_slug": selected_category.slug if selected_category else "",
        "selected_subcategory_slug": selected_subcategory.slug if selected_subcategory else "",
        "trending_products": trending_products,
        "trending_product_cards": trending_product_cards,
        "women_tile_image_url": category_cover_urls.get("women", ""),
        "men_tile_image_url": category_cover_urls.get("men", ""),
        "sale_tile_image_url": category_cover_urls.get("sale", ""),
        "has_new_arrivals": has_new_arrivals,
        "hero_content": hero_content,
    }
    return render(request, "csm/pages/home.html", context)


def help_view(request):
    context = {
        "title": "Help - Italian Luxury Clothing",
        "meta_description": "Get help with your orders, shipping, returns, and more at Italian Luxury Clothing.",
        "cart_count": 0,
        "return_window_days": get_return_window_days(),
    }
    return render(request, "csm/pages/help.html", context)


def returns_view(request):
    context = {
        "title": "Returns - Italian Luxury Clothing",
        "meta_description": "Learn about our return policy and how to return items at Italian Luxury Clothing.",
        "cart_count": 0,
        "return_window_days": get_return_window_days(),
    }
    return render(request, "csm/pages/returns.html", context)


def contact_view(request):
    form_submitted = False

    if request.method == "POST":
        form = PublicInquiryForm(request.POST)
        if form.is_valid():
            submit_inquiry(form.to_dto(consent_ip=request.META.get("REMOTE_ADDR", "")))
            form_submitted = True
            form = PublicInquiryForm()
    else:
        form = PublicInquiryForm()

    context = {
        "title": "Kontakt - Ricotti",
        "meta_description": "Kontaktujte Ricotti. Odpovieme na vaše otázky o produktoch a objednávkach.",
        "cart_count": 0,
        "form": form,
        "form_submitted": form_submitted,
    }
    return render(request, "csm/pages/contact.html", context)
