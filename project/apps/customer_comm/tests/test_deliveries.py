from datetime import timedelta

import pytest
from django.utils import timezone

from apps.customer_comm.constants import DeliveryStatus, PrivacyRequestStatus, PrivacyRequestType
from apps.customer_comm.domain.dtos import SubmitInquiryInput
from apps.customer_comm.application.use_cases import submit_inquiry
from apps.customer_comm.models import PrivacyRequest
from apps.customer_comm.tasks import (
    cleanup_expired_inquiries,
    process_privacy_erasure_request,
    process_privacy_export_request,
    retry_failed_deliveries,
    send_pending_email_delivery,
    send_pending_telegram_delivery,
)


pytestmark = pytest.mark.django_db


def _submit(settings):
    settings.COMMUNICATIONS_ENABLED = True
    settings.EMAIL_PROVIDER = "console"
    settings.EMAIL_FROM_ADDRESS = "shop@example.com"
    settings.EMAIL_TO_ADDRESS = "owner@example.com"
    settings.TELEGRAM_BOT_TOKEN = "token"
    settings.TELEGRAM_CHAT_ID = "123"
    settings.PII_ENCRYPTION_KEY = "secret-key"
    return submit_inquiry(
        SubmitInquiryInput(
            full_name="Jane Doe",
            email="jane@example.com",
            phone="",
            messenger_type="telegram",
            messenger_handle="@jane",
            message="hello",
            consent_given=True,
            consent_ip="127.0.0.1",
            privacy_notice_version="v1",
            consent_text_version="v1",
        )
    )


def test_email_delivery_success(settings):
    inquiry = _submit(settings)
    delivery = inquiry.deliveries.get(channel="email")

    send_pending_email_delivery(delivery.id)

    delivery.refresh_from_db()
    assert delivery.status == DeliveryStatus.SENT
    assert delivery.provider_message_id


def test_telegram_delivery_success(settings, monkeypatch):
    inquiry = _submit(settings)
    delivery = inquiry.deliveries.get(channel="telegram")

    class _Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"result": {"message_id": 99}}

    monkeypatch.setattr("apps.customer_comm.infrastructure.telegram.client.requests.post", lambda *args, **kwargs: _Response())
    send_pending_telegram_delivery(delivery.id)

    delivery.refresh_from_db()
    assert delivery.status == DeliveryStatus.SENT
    assert delivery.provider_message_id == "99"


def test_email_delivery_failure_marks_retryable(settings, monkeypatch):
    inquiry = _submit(settings)
    delivery = inquiry.deliveries.get(channel="email")

    class _Response:
        def raise_for_status(self):
            raise RuntimeError("provider down")

        def json(self):
            return {}

    monkeypatch.setattr("apps.customer_comm.infrastructure.email.providers.requests.post", lambda *args, **kwargs: _Response())
    settings.EMAIL_PROVIDER = "resend"
    settings.EMAIL_PROVIDER_API_KEY = "api-key"

    with pytest.raises(RuntimeError):
        send_pending_email_delivery(delivery.id)

    delivery.refresh_from_db()
    assert delivery.status == DeliveryStatus.FAILED
    assert delivery.attempts == 1


def test_retry_failed_deliveries_dispatches_ready_rows(settings, monkeypatch):
    inquiry = _submit(settings)
    email_delivery = inquiry.deliveries.get(channel="email")
    telegram_delivery = inquiry.deliveries.get(channel="telegram")
    email_delivery.status = DeliveryStatus.FAILED
    email_delivery.next_attempt_at = timezone.now() - timedelta(minutes=1)
    email_delivery.save(update_fields=["status", "next_attempt_at", "updated_at"])
    telegram_delivery.status = DeliveryStatus.FAILED
    telegram_delivery.next_attempt_at = timezone.now() - timedelta(minutes=1)
    telegram_delivery.save(update_fields=["status", "next_attempt_at", "updated_at"])

    dispatched: list[int] = []
    monkeypatch.setattr(
        "apps.customer_comm.tasks.deliveries.send_pending_email_delivery.delay",
        lambda delivery_id: dispatched.append(delivery_id),
    )
    monkeypatch.setattr(
        "apps.customer_comm.tasks.deliveries.send_pending_telegram_delivery.delay",
        lambda delivery_id: dispatched.append(delivery_id),
    )

    count = retry_failed_deliveries()

    assert count == 2
    assert set(dispatched) == {email_delivery.id, telegram_delivery.id}


def test_privacy_export_creates_file(settings):
    inquiry = _submit(settings)
    privacy_request = PrivacyRequest.objects.create(
        inquiry=inquiry,
        request_type=PrivacyRequestType.EXPORT,
        requester_email_hash=inquiry.email_hash,
    )

    process_privacy_export_request(privacy_request.id)

    privacy_request.refresh_from_db()
    assert privacy_request.status == PrivacyRequestStatus.COMPLETED
    assert bool(privacy_request.export_file)


def test_privacy_erasure_anonymizes_inquiry(settings):
    inquiry = _submit(settings)
    privacy_request = PrivacyRequest.objects.create(
        inquiry=inquiry,
        request_type=PrivacyRequestType.ERASURE,
        requester_email_hash=inquiry.email_hash,
    )

    process_privacy_erasure_request(privacy_request.id)

    inquiry.refresh_from_db()
    privacy_request.refresh_from_db()
    assert privacy_request.status == PrivacyRequestStatus.COMPLETED
    assert inquiry.status == "anonymized"
    assert inquiry.email_ciphertext == ""


def test_retention_cleanup_anonymizes_expired_inquiries(settings):
    inquiry = _submit(settings)
    inquiry.retention_expires_at = timezone.now() - timedelta(days=1)
    inquiry.save(update_fields=["retention_expires_at", "updated_at"])

    processed = cleanup_expired_inquiries()

    inquiry.refresh_from_db()
    assert processed == 1
    assert inquiry.status == "anonymized"
