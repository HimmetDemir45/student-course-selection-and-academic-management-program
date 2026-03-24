"""Env-backed feature toggles (settings.FEATURE_FLAGS). See README Phase 8."""

from __future__ import annotations

from django.conf import settings


def is_enabled(flag: str) -> bool:
    flags = getattr(settings, "FEATURE_FLAGS", {})
    return bool(flags.get(flag, False))
