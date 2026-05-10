"""İstek başına şablon bağlamı."""

from django.core.cache import cache


def navigation(request):
    match = getattr(request, "resolver_match", None)
    if not match:
        return {
            "nav_url_name": "",
            "nav_namespace": "",
            "nav_view_name": "",
        }
    return {
        "nav_url_name": match.url_name or "",
        "nav_namespace": match.namespace or "",
        "nav_view_name": f"{match.namespace}:{match.url_name}" if match.namespace else (match.url_name or ""),
    }


def landing_stats(request):
    """Auth split-screen hero panelinde gösterilen agregat sayılar.

    Sadece anonim kullanıcılar için sorgulama yapar (auth ekranını gören kitle).
    60 sn local-memory cache ile DB yükü minimal tutulur.
    """
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return {}

    cached = cache.get("landing_stats:v1")
    if cached is not None:
        return {"landing_stats": cached}

    # Lazy import: app loading ve circular import güvenliği için.
    from academic.models import Announcement
    from courses.models import Course
    from students.models import StudentProfile

    stats = {
        "students": StudentProfile.objects.filter(is_active=True).count(),
        "courses": Course.objects.filter(is_active=True).count(),
        "announcements": Announcement.objects.filter(is_active=True).count(),
    }
    cache.set("landing_stats:v1", stats, timeout=60)
    return {"landing_stats": stats}
