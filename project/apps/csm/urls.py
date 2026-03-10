#project/apps/csm/urls.py
from django.urls import path
from . import views
from django.conf import settings
from django.urls import include


app_name = "pages"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("help/", views.help_view, name="help"),
    path("returns/", views.returns_view, name="returns"),
    path("contact/", views.contact_view, name="contact"),
    
]
