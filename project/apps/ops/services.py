from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import AppLogEntry


def delete_expired_app_logs(*, retention_days: int | None = None) -> int:
    days = retention_days if retention_days is not None else settings.APP_LOG_RETENTION_DAYS
    if days <= 0:
        return 0

    cutoff = timezone.now() - timedelta(days=days)
    deleted, _ = AppLogEntry.objects.filter(created__lt=cutoff).delete()
    return deleted
