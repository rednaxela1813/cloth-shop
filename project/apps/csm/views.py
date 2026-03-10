# project/apps/csm/views.py
from django.conf import settings
from django.shortcuts import render

from apps.products.models import Product
from .forms import ContactMessageForm


def home_view(request):
    trending_products = Product.objects.trending()[:8]

    context = {
        "title": "Italian Luxury Clothing",
        "meta_description": "Nakupujte taliansku módu online – luxusné značky, rýchle doručenie.",
        "cart_count": 0,
        "trending_products": trending_products,
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
