from datetime import timedelta

import pytest
from django.utils import timezone

from apps.ops.models import AppLogEntry
from apps.ops.services import delete_expired_app_logs
from apps.ops.tasks import cleanup_expired_app_logs


pytestmark = pytest.mark.django_db


def test_delete_expired_app_logs_deletes_only_older_entries(settings):
    settings.APP_LOG_RETENTION_DAYS = 30
    old_entry = AppLogEntry.objects.create(
        level="ERROR",
        logger_name="apps.orders.tests",
        event_type="payment.error",
        message="Old incident",
    )
    fresh_entry = AppLogEntry.objects.create(
        level="WARNING",
        logger_name="apps.orders.tests",
        event_type="payment.warning",
        message="Recent incident",
    )

    AppLogEntry.objects.filter(pk=old_entry.pk).update(created=timezone.now() - timedelta(days=31))
    AppLogEntry.objects.filter(pk=fresh_entry.pk).update(created=timezone.now() - timedelta(days=5))

    deleted = delete_expired_app_logs()

    assert deleted == 1
    assert not AppLogEntry.objects.filter(pk=old_entry.pk).exists()
    assert AppLogEntry.objects.filter(pk=fresh_entry.pk).exists()


def test_cleanup_expired_app_logs_task_uses_retention_policy(settings):
    settings.APP_LOG_RETENTION_DAYS = 7
    entry = AppLogEntry.objects.create(
        level="ERROR",
        logger_name="apps.orders.tests",
        event_type="payment.error",
        message="Very old incident",
    )
    AppLogEntry.objects.filter(pk=entry.pk).update(created=timezone.now() - timedelta(days=8))

    deleted = cleanup_expired_app_logs()

    assert deleted == 1
