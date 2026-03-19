from __future__ import annotations

from typing import Protocol

from apps.customer_comm.domain.dtos import ChannelSendResult
from apps.customer_comm.models import Inquiry, InquiryChannelDelivery


class EmailProvider(Protocol):
    provider_name: str

    def send_inquiry_notification(self, *, inquiry: Inquiry, delivery: InquiryChannelDelivery) -> ChannelSendResult:
        ...
