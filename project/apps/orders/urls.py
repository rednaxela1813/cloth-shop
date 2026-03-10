# apps/orders/urls.py
from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.checkout_view, name="checkout"),
    path("pay/<uuid:public_id>/", views.payment_start_view, name="payment_start"),
    path("payment/return/", views.payment_return_view, name="payment_return"),
    path("stripe/webhook/", views.stripe_webhook_view, name="stripe_webhook"),
    path("success/<uuid:public_id>/", views.checkout_success_view, name="success"),
]
