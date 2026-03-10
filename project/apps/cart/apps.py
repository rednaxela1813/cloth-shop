# apps/cart/apps.py
from django.apps import AppConfig


class CartConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cart"

    def ready(self):
        # Import signal handlers on app ready.
        from . import signals  # noqa: F401
