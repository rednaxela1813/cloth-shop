# csm/context_processors.py
from django.db.models import Sum

from apps.cart.models import CartItem
from apps.cart.services import SESSION_CART_ID
from apps.csm.models import FooterContent, SiteBranding


def _cart_count(request) -> int:
    filters = {"cart__is_active": True}

    if request.user.is_authenticated:
        filters["cart__user"] = request.user
    else:
        cart_id = request.session.get(SESSION_CART_ID)
        if cart_id:
            filters["cart_id"] = cart_id
        elif request.session.session_key:
            filters["cart__session_key"] = request.session.session_key
        else:
            return 0

    total = CartItem.objects.filter(**filters).aggregate(total=Sum("quantity"))["total"]
    return int(total or 0)


def ui_context(request):
    branding = SiteBranding.objects.only("site_name", "logo_alt", "logo_original", "logo_header").order_by("id").first()
    footer_content = (
        FooterContent.objects.select_related(
            "shop_women_category",
            "shop_men_category",
            "shop_kids_category",
            "shop_sale_category",
        ).first()
        or FooterContent()
    )

    return {
        "cart_count": _cart_count(request),
        "site_brand_name": branding.site_name if branding else "Ricotti",
        "site_logo_url": branding.resolved_logo_url if branding else "",
        "site_logo_alt": branding.resolved_logo_alt if branding else "Ricotti",
        "footer_content": footer_content,
    }
