from __future__ import annotations

from django.conf import settings

from .base import EmailProvider
from .providers import ConsoleEmailProvider, PostmarkEmailProvider, ResendEmailProvider


def get_email_provider() -> EmailProvider:
    provider = settings.EMAIL_PROVIDER.strip().lower()
    if provider == "resend":
        return ResendEmailProvider(api_key=settings.EMAIL_PROVIDER_API_KEY)
    if provider == "postmark":
        return PostmarkEmailProvider(api_key=settings.EMAIL_PROVIDER_API_KEY)
    return ConsoleEmailProvider()
