# project/apps/catalog/urls.py
from django.urls import path

from apps.catalog import views

app_name = "catalog"

urlpatterns = [
    path("", views.catalog_index_view, name="list"),
    path("<slug:slug>/", views.catalog_category_view, name="category"),
]
