from __future__ import annotations

from uuid import uuid4

from .logging import reset_request_logging_context, set_request_logging_context


class RequestIdMiddleware:
    header_name = "X-Request-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get(self.header_name, "").strip() or uuid4().hex
        request.request_id = request_id

        tokens = set_request_logging_context(
            request_id=request_id,
            method=request.method,
            path=request.get_full_path(),
            remote_addr=request.META.get("REMOTE_ADDR", ""),
        )

        try:
            response = self.get_response(request)
        finally:
            reset_request_logging_context(tokens)

        response[self.header_name] = request_id
        return response
