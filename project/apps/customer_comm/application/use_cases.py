from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.customer_comm.constants import ConsentType, DeliveryChannel, EventType
from apps.customer_comm.domain.dtos import SubmitInquiryInput
from apps.customer_comm.infrastructure.privacy.crypto import (
    encrypt_text,
    mask_email,
    normalize_email,
    normalize_phone,
    stable_hash,
)
from apps.customer_comm.models import ConsentRecord, Inquiry, InquiryChannelDelivery, InquiryEvent
from apps.customer_comm.tasks import send_pending_email_delivery, send_pending_telegram_delivery


def _channel_is_enabled(channel: str) -> bool:
    if not settings.COMMUNICATIONS_ENABLED:
        return False
    if channel == DeliveryChannel.EMAIL:
        return bool(settings.EMAIL_TO_ADDRESS and settings.EMAIL_FROM_ADDRESS)
    if channel == DeliveryChannel.TELEGRAM:
        return bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID)
    return False


def _enqueue_delivery(delivery: InquiryChannelDelivery) -> None:
    if delivery.channel == DeliveryChannel.EMAIL:
        transaction.on_commit(lambda: send_pending_email_delivery.delay(delivery.id))
    elif delivery.channel == DeliveryChannel.TELEGRAM:
        transaction.on_commit(lambda: send_pending_telegram_delivery.delay(delivery.id))


def submit_inquiry(data: SubmitInquiryInput) -> Inquiry:
    if not data.consent_given:
        raise ValueError("Explicit consent is required")

    normalized_email = normalize_email(data.email)
    normalized_phone = normalize_phone(data.phone)
    consent_now = timezone.now()
    retention_expires_at = consent_now + timedelta(days=settings.INQUIRY_RETENTION_DAYS)

    with transaction.atomic():
        inquiry = Inquiry.objects.create(
            full_name_ciphertext=encrypt_text(data.full_name.strip()),
            email_ciphertext=encrypt_text(normalized_email),
            phone_ciphertext=encrypt_text(normalized_phone),
            messenger_type=data.messenger_type,
            messenger_handle_ciphertext=encrypt_text(data.messenger_handle.strip()),
            message_ciphertext=encrypt_text(data.message.strip()),
            email_hash=stable_hash(normalized_email),
            phone_hash=stable_hash(normalized_phone),
            consent_given_at=consent_now,
            consent_ip_hash=stable_hash(data.consent_ip),
            consent_notice_version=data.privacy_notice_version,
            consent_text_version=data.consent_text_version,
            retention_expires_at=retention_expires_at,
        )
        ConsentRecord.objects.create(
            inquiry=inquiry,
            consent_type=ConsentType.CONTACT_INQUIRY,
            granted=True,
            granted_at=consent_now,
            privacy_notice_version=data.privacy_notice_version,
            consent_text_version=data.consent_text_version,
            ip_hash=stable_hash(data.consent_ip),
        )
        InquiryEvent.objects.create(inquiry=inquiry, event_type=EventType.SUBMITTED, metadata={"source": inquiry.source})
        InquiryEvent.objects.create(
            inquiry=inquiry,
            event_type=EventType.CONSENT_RECORDED,
            metadata={"notice_version": data.privacy_notice_version, "text_version": data.consent_text_version},
        )

        deliveries: list[InquiryChannelDelivery] = []
        if _channel_is_enabled(DeliveryChannel.EMAIL):
            deliveries.append(
                InquiryChannelDelivery.objects.create(
                    inquiry=inquiry,
                    channel=DeliveryChannel.EMAIL,
                    provider=settings.EMAIL_PROVIDER,
                    destination_summary=mask_email(settings.EMAIL_TO_ADDRESS),
                    payload={"source": inquiry.source},
                    max_attempts=settings.INQUIRY_MAX_DELIVERY_ATTEMPTS,
                )
            )
        if _channel_is_enabled(DeliveryChannel.TELEGRAM):
            deliveries.append(
                InquiryChannelDelivery.objects.create(
                    inquiry=inquiry,
                    channel=DeliveryChannel.TELEGRAM,
                    provider="telegram_bot_api",
                    destination_summary=settings.TELEGRAM_CHAT_ID,
                    payload={"source": inquiry.source},
                    max_attempts=settings.INQUIRY_MAX_DELIVERY_ATTEMPTS,
                )
            )
        for delivery in deliveries:
            InquiryEvent.objects.create(
                inquiry=inquiry,
                event_type=EventType.DELIVERY_QUEUED,
                metadata={"channel": delivery.channel, "provider": delivery.provider},
            )
            _enqueue_delivery(delivery)

    return inquiry
