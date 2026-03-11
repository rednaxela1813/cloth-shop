# csm/context_processors.py
from django.db.models import Sum

from apps.cart.models import CartItem
from apps.cart.services import SESSION_CART_ID


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
    return {
        "cart_count": _cart_count(request),
    }
