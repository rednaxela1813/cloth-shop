from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone

from .constants import (
    ConsentType,
    DeliveryChannel,
    DeliveryStatus,
    EventType,
    InquirySource,
    InquiryStatus,
    MessengerType,
    PrivacyRequestStatus,
    PrivacyRequestType,
)


class Inquiry(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    source = models.CharField(max_length=40, choices=InquirySource.choices, default=InquirySource.WEBSITE_CONTACT)
    status = models.CharField(max_length=20, choices=InquiryStatus.choices, default=InquiryStatus.RECEIVED)
    full_name_ciphertext = models.TextField(blank=True)
    email_ciphertext = models.TextField(blank=True)
    phone_ciphertext = models.TextField(blank=True)
    messenger_type = models.CharField(max_length=40, choices=MessengerType.choices, blank=True)
    messenger_handle_ciphertext = models.TextField(blank=True)
    message_ciphertext = models.TextField(blank=True)
    email_hash = models.CharField(max_length=64, db_index=True)
    phone_hash = models.CharField(max_length=64, blank=True, db_index=True)
    consent_given_at = models.DateTimeField()
    consent_ip_hash = models.CharField(max_length=64, blank=True)
    consent_notice_version = models.CharField(max_length=32)
    consent_text_version = models.CharField(max_length=32)
    retention_expires_at = models.DateTimeField(db_index=True)
    anonymized_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    last_exported_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status", "retention_expires_at"]),
            models.Index(fields=["source", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Inquiry {self.public_id}"

    def anonymize(self) -> None:
        self.full_name_ciphertext = ""
        self.email_ciphertext = ""
        self.phone_ciphertext = ""
        self.messenger_handle_ciphertext = ""
        self.message_ciphertext = ""
        self.status = InquiryStatus.ANONYMIZED
        self.anonymized_at = timezone.now()


class ConsentRecord(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name="consent_records")
    consent_type = models.CharField(max_length=40, choices=ConsentType.choices, default=ConsentType.CONTACT_INQUIRY)
    granted = models.BooleanField(default=True)
    granted_at = models.DateTimeField()
    privacy_notice_version = models.CharField(max_length=32)
    consent_text_version = models.CharField(max_length=32)
    ip_hash = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"Consent {self.public_id}"


class InquiryChannelDelivery(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name="deliveries")
    channel = models.CharField(max_length=20, choices=DeliveryChannel.choices)
    provider = models.CharField(max_length=64)
    status = models.CharField(max_length=20, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)
    destination_summary = models.CharField(max_length=255, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    next_attempt_at = models.DateTimeField(default=timezone.now, db_index=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    provider_message_id = models.CharField(max_length=255, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "next_attempt_at", "id"]
        indexes = [
            models.Index(fields=["channel", "status", "next_attempt_at"]),
            models.Index(fields=["inquiry", "channel"]),
        ]

    def __str__(self) -> str:
        return f"{self.channel}:{self.status}:{self.public_id}"


class InquiryEvent(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name="events", null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=EventType.choices)
    actor = models.CharField(max_length=64, default="system")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["inquiry", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type}:{self.public_id}"


class PrivacyRequest(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    inquiry = models.ForeignKey(Inquiry, on_delete=models.SET_NULL, related_name="privacy_requests", null=True, blank=True)
    request_type = models.CharField(max_length=20, choices=PrivacyRequestType.choices)
    status = models.CharField(max_length=20, choices=PrivacyRequestStatus.choices, default=PrivacyRequestStatus.PENDING)
    requester_email_hash = models.CharField(max_length=64, db_index=True)
    export_file = models.FileField(upload_to="customer-comm/privacy-exports/", blank=True, null=True)
    failure_reason = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-requested_at", "-id"]
        indexes = [
            models.Index(fields=["request_type", "status"]),
            models.Index(fields=["requester_email_hash", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.request_type}:{self.public_id}"
