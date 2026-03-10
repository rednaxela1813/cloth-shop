# apps/products/urls.py
from django.urls import path
from apps.products import views

app_name = "products"

urlpatterns = [
    path("", views.product_list_view, name="list"),
    path("<uuid:public_id>/<slug:slug>/", views.product_detail_view, name="detail"),
]
