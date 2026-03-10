# csm/context_processors.py
from django.db.models import Sum

from apps.cart.models import Cart
from apps.cart.services import SESSION_CART_ID


def _cart_count(request) -> int:
    cart = None
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user, is_active=True).first()
    else:
        cart_id = request.session.get(SESSION_CART_ID)
        if cart_id:
            cart = Cart.objects.filter(id=cart_id, is_active=True).first()
        elif request.session.session_key:
            cart = Cart.objects.filter(session_key=request.session.session_key, is_active=True).first()

    if not cart:
        return 0

    total = cart.items.aggregate(total=Sum("quantity"))["total"]
    return int(total or 0)


def ui_context(request):
    return {
        "cart_count": _cart_count(request),
    }
