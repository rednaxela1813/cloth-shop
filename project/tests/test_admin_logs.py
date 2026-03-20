import logging

import pytest

from apps.ops.models import AppLogEntry
from ital.logging import DatabaseLogHandler, RequestContextFilter


pytestmark = pytest.mark.django_db


def test_database_log_handler_persists_warning_record():
    logger = logging.getLogger("apps.orders.tests")
    record = logger.makeRecord(
        name=logger.name,
        level=logging.WARNING,
        fn=__file__,
        lno=21,
        msg="Gateway returned warning",
        args=(),
        exc_info=None,
        extra={
            "event_type": "payment.gateway.warning",
            "request_id": "req-789",
            "request_method": "POST",
            "request_path": "/checkout/payment/start/",
            "remote_addr": "127.0.0.1",
            "order_public_id": "order-22",
        },
    )
    RequestContextFilter().filter(record)

    DatabaseLogHandler().emit(record)

    entry = AppLogEntry.objects.get()
    assert entry.level == "WARNING"
    assert entry.logger_name == "apps.orders.tests"
    assert entry.event_type == "payment.gateway.warning"
    assert entry.request_id == "req-789"
    assert entry.payload["order_public_id"] == "order-22"
