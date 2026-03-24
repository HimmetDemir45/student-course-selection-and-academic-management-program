"""
Low-risk read-mostly aggregates with short TTL (LocMem in dev; swap to Redis in prod if needed).
"""

from __future__ import annotations

from django.core.cache import cache

from courses.models import CourseOffering

HOME_ACTIVE_OFFERINGS_KEY = "phase6:home:active_offering_count"
HOME_ACTIVE_OFFERINGS_TTL = 60


def cached_active_offering_count() -> int:
    """Count of active course offerings; cached to avoid repeated COUNT(*) on hot paths."""
    cached = cache.get(HOME_ACTIVE_OFFERINGS_KEY)
    if cached is not None:
        return int(cached)
    n = CourseOffering.objects.filter(is_active=True).count()
    cache.set(HOME_ACTIVE_OFFERINGS_KEY, n, HOME_ACTIVE_OFFERINGS_TTL)
    return n
