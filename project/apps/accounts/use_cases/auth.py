from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate


def authenticate_customer(*, request, email: str, password: str):
    email_value = (email or "").strip().lower()
    if not email_value or not password:
        return None
    return authenticate(request=request, email=email_value, password=password)


def create_customer_account(*, email: str, password: str):
    user_model = get_user_model()
    return user_model.objects.create_user(
        email=(email or "").strip().lower(),
        password=password,
        is_staff=False,
        is_superuser=False,
    )
