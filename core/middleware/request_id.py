"""
X-Request-ID propagation, per-request log context, and structured request_finished line.
Prod JSON: structlog contextvars + JSON LOGGING (DJANGO_LOG_JSON=True).
Dev: contextvars + stdlib logger (see core.request_context).
"""

from __future__ import annotations

import logging
import time
import uuid

from django.conf import settings

from core.request_context import bind_request_log_context, clear_request_log_context

REQUEST_ID_HEADER = "X-Request-ID"
INBOUND_META_KEY = "HTTP_X_REQUEST_ID"
logger = logging.getLogger("request")


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.META.get(INBOUND_META_KEY, "").strip()
        rid = incoming[:128] if incoming else str(uuid.uuid4())
        request.request_id = rid
        start = time.perf_counter()

        service = getattr(settings, "LOG_SERVICE_NAME", "student-academic-mgmt")

        if getattr(settings, "DJANGO_LOG_JSON", False):
            import structlog.contextvars

            structlog.contextvars.bind_contextvars(
                request_id=rid,
                http_path=request.path,
                http_method=request.method,
                service=service,
            )
        else:
            bind_request_log_context(request_id=rid, path=request.path, method=request.method)

        response = None
        try:
            response = self.get_response(request)
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            status = getattr(response, "status_code", 500) if response is not None else 500
            uid = None
            if hasattr(request, "user") and getattr(request.user, "is_authenticated", False):
                uid = request.user.pk

            if getattr(settings, "DJANGO_LOG_JSON", False):
                import structlog
                import structlog.contextvars

                structlog.get_logger("request").info(
                    "request_finished",
                    status_code=status,
                    duration_ms=duration_ms,
                    user_id=uid,
                    service=service,
                )
                structlog.contextvars.clear_contextvars()
            else:
                logger.info(
                    "request_finished service=%s status=%s duration_ms=%s user_id=%s",
                    service,
                    status,
                    duration_ms,
                    uid,
                )
                clear_request_log_context()

            if response is not None:
                response[REQUEST_ID_HEADER] = rid
