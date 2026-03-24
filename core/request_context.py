"""Per-request fields for stdlib logging when DJANGO_LOG_JSON is False."""

from __future__ import annotations

import contextvars

_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("log_request_id", default=None)
_http_path: contextvars.ContextVar[str | None] = contextvars.ContextVar("log_http_path", default=None)
_http_method: contextvars.ContextVar[str | None] = contextvars.ContextVar("log_http_method", default=None)


def bind_request_log_context(*, request_id: str, path: str, method: str) -> None:
    _request_id.set(request_id)
    _http_path.set(path)
    _http_method.set(method)


def clear_request_log_context() -> None:
    _request_id.set(None)
    _http_path.set(None)
    _http_method.set(None)


class RequestContextFilter:
    """Injects request_id / path / method into LogRecord for text formatters."""

    def filter(self, record) -> bool:
        record.request_id = _request_id.get() or "-"
        record.http_path = _http_path.get() or "-"
        record.http_method = _http_method.get() or "-"
        return True
