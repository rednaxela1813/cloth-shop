from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SubmitInquiryInput:
    full_name: str
    email: str
    phone: str
    messenger_type: str
    messenger_handle: str
    message: str
    consent_given: bool
    consent_ip: str
    privacy_notice_version: str
    consent_text_version: str


@dataclass(frozen=True)
class ChannelSendResult:
    provider_message_id: str

