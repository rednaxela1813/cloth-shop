from __future__ import annotations

import json
from django.core.files.base import ContentFile
from django.utils import timezone

from apps.customer_comm.infrastructure.privacy.crypto import decrypt_text
from apps.customer_comm.models import Inquiry, PrivacyRequest


def build_inquiry_export_payload(inquiry: Inquiry) -> dict:
    return {
        "public_id": str(inquiry.public_id),
        "source": inquiry.source,
        "status": inquiry.status,
        "full_name": decrypt_text(inquiry.full_name_ciphertext),
        "email": decrypt_text(inquiry.email_ciphertext),
        "phone": decrypt_text(inquiry.phone_ciphertext),
        "messenger_type": inquiry.messenger_type,
        "messenger_handle": decrypt_text(inquiry.messenger_handle_ciphertext),
        "message": decrypt_text(inquiry.message_ciphertext),
        "consent_given_at": inquiry.consent_given_at.isoformat(),
        "consent_notice_version": inquiry.consent_notice_version,
        "consent_text_version": inquiry.consent_text_version,
        "created_at": inquiry.created_at.isoformat(),
    }


def store_privacy_export(*, privacy_request: PrivacyRequest, payload: dict) -> None:
    filename = f"inquiry-export-{privacy_request.public_id}.json"
    content = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    privacy_request.export_file.save(filename, ContentFile(content), save=False)
    privacy_request.completed_at = timezone.now()


def anonymize_inquiry(inquiry: Inquiry) -> None:
    inquiry.anonymize()
    inquiry.save(
        update_fields=[
            "full_name_ciphertext",
            "email_ciphertext",
            "phone_ciphertext",
            "messenger_handle_ciphertext",
            "message_ciphertext",
            "status",
            "anonymized_at",
            "updated_at",
        ]
    )


def delete_inquiry(inquiry: Inquiry) -> None:
    inquiry.deleted_at = timezone.now()
    inquiry.status = "deleted"
    inquiry.save(update_fields=["deleted_at", "status", "updated_at"])
