"""
Structured JSON logging for production (DJANGO_LOG_JSON=True).
Field reference: docs/observability.md
"""

from __future__ import annotations

import re

import structlog

_REDACT_KEYS = frozenset(
    {"password", "authorization", "cookie", "secret", "api_key", "token", "access_token"}
)


def _redact_event_dict(_logger, _name, event_dict: dict) -> dict:
    for k in list(event_dict.keys()):
        lk = k.lower()
        if lk in _REDACT_KEYS or "password" in lk or "secret" in lk or "token" in lk:
            event_dict[k] = "***"
    msg = event_dict.get("event")
    if isinstance(msg, str):
        for pattern, repl in (
            (re.compile(r"(?i)(password|secret|token|api_key)\s*[=:]\s*\S+"), r"\1=***"),
            (re.compile(r"(?i)(mysql://|postgresql://)([^:@\s]+):([^@\s/]+)@"), r"\1\2:***@"),
        ):
            msg = pattern.sub(repl, msg)
        event_dict["event"] = msg
    return event_dict


def build_foreign_pre_chain() -> list:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", key="timestamp"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        _redact_event_dict,
    ]


def init_structlog_for_json_logging() -> None:
    structlog.configure(
        processors=build_foreign_pre_chain()
        + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_json_logging_dict(log_level: str) -> dict:
    pre = build_foreign_pre_chain()
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
                "foreign_pre_chain": pre,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": log_level,
        },
        "loggers": {
            "django": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "django.request": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "request": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
        },
    }
