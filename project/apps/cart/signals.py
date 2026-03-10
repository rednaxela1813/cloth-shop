# apps/cart/signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .services import merge_session_cart_to_user


@receiver(user_logged_in)
def merge_cart_on_login(sender, request, user, **kwargs):
    # Keep cart continuity for anonymous users after authentication.
    merge_session_cart_to_user(user, request.session)
