from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.account_login_view, name="login"),
    path("register/", views.account_register_view, name="register"),
    path("logout/", views.account_logout_view, name="logout"),
    path("", views.account_dashboard_view, name="dashboard"),
    path("orders/", views.account_orders_view, name="orders"),
]
