from __future__ import annotations

from dataclasses import dataclass

import requests
from django.conf import settings

from apps.customer_comm.domain.dtos import ChannelSendResult
from apps.customer_comm.infrastructure.email.base import EmailProvider
from apps.customer_comm.infrastructure.privacy.crypto import decrypt_text
from apps.customer_comm.models import Inquiry, InquiryChannelDelivery


def _build_email_subject(*, inquiry: Inquiry) -> str:
    return f"New website inquiry {inquiry.public_id}"


def _build_email_text(*, inquiry: Inquiry) -> str:
    return "\n".join(
        [
            "A new contact form inquiry has been submitted.",
            f"Inquiry ID: {inquiry.public_id}",
            f"Name: {decrypt_text(inquiry.full_name_ciphertext) or '-'}",
            f"Email: {decrypt_text(inquiry.email_ciphertext)}",
            f"Phone: {decrypt_text(inquiry.phone_ciphertext) or '-'}",
            f"Messenger: {inquiry.messenger_type or '-'}",
            f"Messenger handle: {decrypt_text(inquiry.messenger_handle_ciphertext) or '-'}",
            "",
            "Message:",
            decrypt_text(inquiry.message_ciphertext),
        ]
    )


@dataclass
class ConsoleEmailProvider:
    provider_name: str = "console"

    def send_inquiry_notification(self, *, inquiry: Inquiry, delivery: InquiryChannelDelivery) -> ChannelSendResult:
        return ChannelSendResult(provider_message_id=f"console-{delivery.public_id}")


@dataclass
class ResendEmailProvider:
    api_key: str
    provider_name: str = "resend"

    def send_inquiry_notification(self, *, inquiry: Inquiry, delivery: InquiryChannelDelivery) -> ChannelSendResult:
        response = requests.post(
            settings.EMAIL_PROVIDER_API_URL or "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.EMAIL_FROM_ADDRESS,
                "to": [settings.EMAIL_TO_ADDRESS],
                "subject": _build_email_subject(inquiry=inquiry),
                "text": _build_email_text(inquiry=inquiry),
            },
            timeout=settings.EMAIL_PROVIDER_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        return ChannelSendResult(provider_message_id=payload.get("id", ""))


@dataclass
class PostmarkEmailProvider:
    api_key: str
    provider_name: str = "postmark"

    def send_inquiry_notification(self, *, inquiry: Inquiry, delivery: InquiryChannelDelivery) -> ChannelSendResult:
        response = requests.post(
            settings.EMAIL_PROVIDER_API_URL or "https://api.postmarkapp.com/email",
            headers={
                "X-Postmark-Server-Token": self.api_key,
                "Content-Type": "application/json",
            },
            json={
                "From": settings.EMAIL_FROM_ADDRESS,
                "To": settings.EMAIL_TO_ADDRESS,
                "Subject": _build_email_subject(inquiry=inquiry),
                "TextBody": _build_email_text(inquiry=inquiry),
            },
            timeout=settings.EMAIL_PROVIDER_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        return ChannelSendResult(provider_message_id=str(payload.get("MessageID", "")))
