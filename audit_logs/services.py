from audit_logs.models import AuditLog


def _extract_ip(request):
    if not request:
        return None

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_auth_event(event_type, user=None, request=None, description=""):
    """
    Auth olaylarini sistem akisini bozmadan loglar.
    """
    try:
        AuditLog.objects.create(
            user=user if getattr(user, "is_authenticated", False) else None,
            event_type=event_type,
            description=description,
            ip_address=_extract_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
        )
    except Exception:
        # Log hatasi auth akisinin calismasini engellememeli.
        return None
