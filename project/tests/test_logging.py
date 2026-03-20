import json
import logging

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from ital.logging import JsonFormatter, RequestContextFilter
from ital.middleware import RequestIdMiddleware


class RequestIdMiddlewareTests(SimpleTestCase):
    def test_middleware_sets_request_id_header(self):
        request = RequestFactory().get("/healthz", HTTP_X_REQUEST_ID="req-123")
        middleware = RequestIdMiddleware(lambda req: HttpResponse("ok"))

        response = middleware(request)

        assert response["X-Request-ID"] == "req-123"
        assert request.request_id == "req-123"


class JsonFormatterTests(SimpleTestCase):
    def test_json_formatter_includes_request_context_and_extra_fields(self):
        logger = logging.getLogger("tests.logging")
        record = logger.makeRecord(
            name=logger.name,
            level=logging.INFO,
            fn=__file__,
            lno=42,
            msg="Payment started",
            args=(),
            exc_info=None,
            extra={
                "request_id": "req-456",
                "request_method": "POST",
                "request_path": "/checkout/payment/start/",
                "event_type": "payment.start",
                "order_public_id": "order-1",
            },
        )
        RequestContextFilter().filter(record)

        payload = json.loads(JsonFormatter().format(record))

        assert payload["message"] == "Payment started"
        assert payload["request_id"] == "req-456"
        assert payload["request_method"] == "POST"
        assert payload["request_path"] == "/checkout/payment/start/"
        assert payload["event_type"] == "payment.start"
        assert payload["order_public_id"] == "order-1"
