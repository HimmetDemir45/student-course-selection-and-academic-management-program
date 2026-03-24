"""
Propagate X-Request-ID for log/trace correlation (ALB, CloudWatch, downstream services).
Client may send X-Request-ID; otherwise a UUID is assigned.
"""

from __future__ import annotations

import uuid

from django.utils.deprecation import MiddlewareMixin

REQUEST_ID_HEADER = "X-Request-ID"
INBOUND_META_KEY = "HTTP_X_REQUEST_ID"


class RequestIdMiddleware(MiddlewareMixin):
    def process_request(self, request):
        incoming = request.META.get(INBOUND_META_KEY, "").strip()
        request.request_id = incoming[:128] if incoming else str(uuid.uuid4())
        return None

    def process_response(self, request, response):
        rid = getattr(request, "request_id", None)
        if rid:
            response[REQUEST_ID_HEADER] = rid
        return response
