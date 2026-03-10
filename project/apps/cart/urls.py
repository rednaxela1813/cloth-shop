# apps/cart/urls.py
from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_detail_view, name="detail"),
    path("add/<uuid:public_id>/", views.cart_add_view, name="add"),
    path("add/", views.cart_add_by_variant_view, name="add_by_variant"),
    path("remove/<uuid:public_id>/", views.cart_remove_view, name="remove"),
    path("set/<uuid:public_id>/", views.cart_set_quantity_view, name="set_quantity"),
    path("clear/", views.cart_clear_view, name="clear"),
]
