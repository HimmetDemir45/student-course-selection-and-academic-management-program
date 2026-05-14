"""
Brute-force giriş denemelerini sınırlayan throttle servisi (kullanıcı/IP bazlı sayaç).
"""
from __future__ import annotations

from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect


def _max_failures() -> int:
    return int(getattr(settings, "LOGIN_THROTTLE_MAX_FAILURES", 5))


def _lockout_seconds() -> int:
    return int(getattr(settings, "LOGIN_THROTTLE_LOCKOUT_SECONDS", 900))


def get_client_ip(request) -> str:
    """Client IP for throttle keys; values bounded to avoid cache key abuse via huge headers."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        if len(xff) > 256:
            xff = xff[:256]
        first = xff.split(",")[0].strip()
        return (first[:45] if first else "unknown") or "unknown"
    raw = request.META.get("REMOTE_ADDR", "") or ""
    return raw[:45] if raw else "unknown"


def _identity_key(raw_login: str) -> str:
    return (raw_login or "").strip().lower()[:150] or "anonymous"


def is_login_locked(request, raw_login: str) -> bool:
    ip = get_client_ip(request)
    key = _identity_key(raw_login)
    return cache.get(f"login_lock:{ip}:{key}") is not None


def register_login_failure(request, raw_login: str) -> None:
    ip = get_client_ip(request)
    key = _identity_key(raw_login)
    fail_key = f"login_fail:{ip}:{key}"
    n = int(cache.get(fail_key) or 0) + 1
    cache.set(fail_key, n, _lockout_seconds())
    if n >= _max_failures():
        cache.set(f"login_lock:{ip}:{key}", True, _lockout_seconds())


def clear_login_throttle(request, raw_login: str) -> None:
    ip = get_client_ip(request)
    key = _identity_key(raw_login)
    cache.delete(f"login_fail:{ip}:{key}")
    cache.delete(f"login_lock:{ip}:{key}")


def login_throttle(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.method == "POST":
            raw = request.POST.get("login", "")
            if is_login_locked(request, raw):
                messages.error(
                    request,
                    "Cok fazla basarisiz giris denemesi. Lutfen daha sonra tekrar deneyin.",
                )
                return redirect("accounts:login")
        return view_func(request, *args, **kwargs)

    return _wrapped
