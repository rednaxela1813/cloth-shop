from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.customer_comm.constants import DeliveryChannel, DeliveryStatus, EventType, PrivacyRequestStatus, PrivacyRequestType
from apps.customer_comm.infrastructure.email.factory import get_email_provider
from apps.customer_comm.infrastructure.privacy.service import (
    anonymize_inquiry,
    build_inquiry_export_payload,
    delete_inquiry,
    store_privacy_export,
)
from apps.customer_comm.infrastructure.telegram.factory import get_telegram_provider
from apps.customer_comm.models import InquiryChannelDelivery, InquiryEvent, PrivacyRequest
from apps.customer_comm.selectors import expired_inquiries, pending_deliveries
from apps.customer_comm.tasks.compat import shared_task


def _backoff_seconds(attempt: int) -> int:
    return settings.INQUIRY_RETRY_BASE_DELAY_SECONDS * max(attempt, 1)


def _mark_delivery_failed(delivery: InquiryChannelDelivery, exc: Exception) -> None:
    delivery.last_error = str(exc)
    delivery.status = DeliveryStatus.EXHAUSTED if delivery.attempts >= delivery.max_attempts else DeliveryStatus.FAILED
    delivery.next_attempt_at = timezone.now() + timedelta(seconds=_backoff_seconds(delivery.attempts))
    delivery.locked_at = None
    delivery.save(update_fields=["last_error", "status", "next_attempt_at", "locked_at", "updated_at"])
    InquiryEvent.objects.create(
        inquiry=delivery.inquiry,
        event_type=EventType.DELIVERY_FAILED,
        metadata={"channel": delivery.channel, "status": delivery.status},
    )


def _deliver(*, delivery_id: int, channel: str) -> None:
    with transaction.atomic():
        delivery = InquiryChannelDelivery.objects.select_for_update().select_related("inquiry").get(pk=delivery_id)
        if delivery.channel != channel or delivery.status not in {DeliveryStatus.PENDING, DeliveryStatus.FAILED}:
            return
        delivery.status = DeliveryStatus.IN_PROGRESS
        delivery.attempts += 1
        delivery.last_attempt_at = timezone.now()
        delivery.locked_at = timezone.now()
        delivery.save(update_fields=["status", "attempts", "last_attempt_at", "locked_at", "updated_at"])

    try:
        if channel == DeliveryChannel.EMAIL:
            result = get_email_provider().send_inquiry_notification(inquiry=delivery.inquiry, delivery=delivery)
        else:
            result = get_telegram_provider().send_inquiry_notification(inquiry=delivery.inquiry, delivery=delivery)
    except Exception as exc:
        _mark_delivery_failed(delivery, exc)
        raise

    delivery.provider_message_id = result.provider_message_id
    delivery.sent_at = timezone.now()
    delivery.status = DeliveryStatus.SENT
    delivery.locked_at = None
    delivery.last_error = ""
    delivery.save(update_fields=["provider_message_id", "sent_at", "status", "locked_at", "last_error", "updated_at"])
    InquiryEvent.objects.create(
        inquiry=delivery.inquiry,
        event_type=EventType.DELIVERY_SENT,
        metadata={"channel": delivery.channel, "provider": delivery.provider},
    )


@shared_task(name="apps.customer_comm.tasks.send_pending_email_delivery")
def send_pending_email_delivery(delivery_id: int) -> None:
    _deliver(delivery_id=delivery_id, channel=DeliveryChannel.EMAIL)


@shared_task(name="apps.customer_comm.tasks.send_pending_telegram_delivery")
def send_pending_telegram_delivery(delivery_id: int) -> None:
    _deliver(delivery_id=delivery_id, channel=DeliveryChannel.TELEGRAM)


@shared_task(name="apps.customer_comm.tasks.retry_failed_deliveries")
def retry_failed_deliveries() -> int:
    count = 0
    for delivery in pending_deliveries(channel=DeliveryChannel.EMAIL):
        send_pending_email_delivery.delay(delivery.id)
        count += 1
    for delivery in pending_deliveries(channel=DeliveryChannel.TELEGRAM):
        send_pending_telegram_delivery.delay(delivery.id)
        count += 1
    return count


@shared_task(name="apps.customer_comm.tasks.cleanup_expired_inquiries")
def cleanup_expired_inquiries() -> int:
    count = 0
    for inquiry in expired_inquiries():
        if settings.INQUIRY_ANONYMIZE_INSTEAD_OF_DELETE:
            anonymize_inquiry(inquiry)
            InquiryEvent.objects.create(inquiry=inquiry, event_type=EventType.RETENTION_ANONYMIZED)
        else:
            delete_inquiry(inquiry)
            InquiryEvent.objects.create(inquiry=inquiry, event_type=EventType.RETENTION_DELETED)
        count += 1
    return count


@shared_task(name="apps.customer_comm.tasks.process_privacy_export_request")
def process_privacy_export_request(privacy_request_id: int) -> None:
    privacy_request = PrivacyRequest.objects.select_related("inquiry").get(pk=privacy_request_id)
    privacy_request.status = PrivacyRequestStatus.PROCESSING
    privacy_request.started_at = timezone.now()
    privacy_request.save(update_fields=["status", "started_at", "updated_at"])
    try:
        payload = build_inquiry_export_payload(privacy_request.inquiry)
        store_privacy_export(privacy_request=privacy_request, payload=payload)
        privacy_request.status = PrivacyRequestStatus.COMPLETED
        privacy_request.save(update_fields=["status", "completed_at", "export_file", "updated_at"])
        privacy_request.inquiry.last_exported_at = timezone.now()
        privacy_request.inquiry.save(update_fields=["last_exported_at", "updated_at"])
        InquiryEvent.objects.create(inquiry=privacy_request.inquiry, event_type=EventType.PRIVACY_EXPORT_COMPLETED)
    except Exception as exc:
        privacy_request.status = PrivacyRequestStatus.FAILED
        privacy_request.failure_reason = str(exc)
        privacy_request.save(update_fields=["status", "failure_reason", "updated_at"])
        raise


@shared_task(name="apps.customer_comm.tasks.process_privacy_erasure_request")
def process_privacy_erasure_request(privacy_request_id: int) -> None:
    privacy_request = PrivacyRequest.objects.select_related("inquiry").get(pk=privacy_request_id)
    privacy_request.status = PrivacyRequestStatus.PROCESSING
    privacy_request.started_at = timezone.now()
    privacy_request.save(update_fields=["status", "started_at", "updated_at"])
    try:
        if settings.INQUIRY_ANONYMIZE_INSTEAD_OF_DELETE:
            anonymize_inquiry(privacy_request.inquiry)
        else:
            delete_inquiry(privacy_request.inquiry)
        privacy_request.status = PrivacyRequestStatus.COMPLETED
        privacy_request.completed_at = timezone.now()
        privacy_request.save(update_fields=["status", "completed_at", "updated_at"])
        InquiryEvent.objects.create(inquiry=privacy_request.inquiry, event_type=EventType.PRIVACY_ERASURE_COMPLETED)
    except Exception as exc:
        privacy_request.status = PrivacyRequestStatus.FAILED
        privacy_request.failure_reason = str(exc)
        privacy_request.save(update_fields=["status", "failure_reason", "updated_at"])
        raise
