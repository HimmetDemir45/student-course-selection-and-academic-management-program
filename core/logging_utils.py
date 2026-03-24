"""
Safe logging helpers: reduce accidental secret leakage in formatted log lines.
"""

from __future__ import annotations

import logging
import re

_REDACT_RES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)(password|passwd|pwd|secret|api[_-]?key|token|authorization)(['\"]=?|:|\s*=\s*)(\S+?)"), r"\1\2***"),
    (re.compile(r"(?i)(mysql://|postgresql://)([^:@\s]+):([^@\s/]+)@"), r"\1\2:***@"),
)


def redact_message(text: str) -> str:
    out = text
    for pattern, repl in _REDACT_RES:
        out = pattern.sub(repl, out)
    return out


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return redact_message(super().format(record))
