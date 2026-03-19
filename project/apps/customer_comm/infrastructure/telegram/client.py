from __future__ import annotations

from dataclasses import dataclass

import requests
from django.conf import settings

from apps.customer_comm.domain.dtos import ChannelSendResult
from apps.customer_comm.infrastructure.privacy.crypto import decrypt_text
from apps.customer_comm.models import Inquiry, InquiryChannelDelivery


def _build_message(*, inquiry: Inquiry) -> str:
    return "\n".join(
        [
            "New website inquiry",
            f"ID: {inquiry.public_id}",
            f"Name: {decrypt_text(inquiry.full_name_ciphertext) or '-'}",
            f"Email: {decrypt_text(inquiry.email_ciphertext)}",
            f"Phone: {decrypt_text(inquiry.phone_ciphertext) or '-'}",
            f"Messenger: {inquiry.messenger_type or '-'}",
            f"Handle: {decrypt_text(inquiry.messenger_handle_ciphertext) or '-'}",
            "Message:",
            decrypt_text(inquiry.message_ciphertext),
        ]
    )


@dataclass
class TelegramBotProvider:
    provider_name: str = "telegram_bot_api"

    def send_inquiry_notification(self, *, inquiry: Inquiry, delivery: InquiryChannelDelivery) -> ChannelSendResult:
        response = requests.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": _build_message(inquiry=inquiry),
            },
            timeout=settings.EMAIL_PROVIDER_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        result = payload.get("result", {})
        return ChannelSendResult(provider_message_id=str(result.get("message_id", "")))
