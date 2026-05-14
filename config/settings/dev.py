"""
Geliştirme ortamı ayarları (DEBUG=True, console email, SQLite/MySQL fallback).
"""
import sys

from .base import *  # noqa: F403,F401

_PYTEST_LOADED = "pytest" in sys.modules

SECRET_KEY = env(  # noqa: F405
    "DJANGO_SECRET_KEY",
    default=env("SECRET_KEY", default="django-insecure-dev-only-change-me"),  # noqa: F405
)

DEBUG = env.bool("DJANGO_DEBUG", default=env.bool("DEBUG", default=True))  # noqa: F405

ALLOWED_HOSTS = env.list(  # noqa: F405
    "DJANGO_ALLOWED_HOSTS",
    default=env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"]),
)

# Yerel geliştiricide Origin/HTTPS varyasyonlarında CSRF doğrulamasının düşmesini önlemek için
# varsayılan kökenler; üretimde prod.py kullanılır (.env ile üzerine yazılabilir).
CSRF_TRUSTED_ORIGINS = env.list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    default=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://[::1]:8000",
        "http://testserver",  # Django test istemcisinin gönderdiği Origin/Referrer
    ],
)

if "test" in sys.argv or _PYTEST_LOADED:
    # core/urls.py test rotalari: DEBUG kapali olsa da testlerde reverse() calissin.
    # Rollback: bu satiri silin; prod etkilenmez (prod.py bu blogu import etmez).
    INCLUDE_CORE_DEV_TEST_ROUTES = True
    DATABASES["default"] = {  # noqa: F405
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
    RATELIMIT_ENABLE = False  # noqa: F405
    # Beklenen 403/CSRF testlerinde django.request / security log gürültüsünü azalt
    _lg = LOGGING.setdefault("loggers", {})  # noqa: F405
    _lg["django.request"] = {"handlers": ["console"], "level": "ERROR", "propagate": False}
    _lg["django.security.csrf"] = {"handlers": ["console"], "level": "ERROR", "propagate": False}
    _lg["request"] = {"handlers": ["console"], "level": "WARNING", "propagate": False}

# E-posta: SMTP kimlik bilgileri varsa gerçek posta gönder, yoksa konsola yaz.
_email_host_user = env("EMAIL_HOST_USER", default="")  # noqa: F405
if _email_host_user:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")  # noqa: F405
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)  # noqa: F405
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)  # noqa: F405
    EMAIL_HOST_USER = _email_host_user
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")  # noqa: F405
    DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default=_email_host_user)  # noqa: F405
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

if sys.version_info >= (3, 14) and ("test" in sys.argv or _PYTEST_LOADED):
    from core.test_client_context_patch import apply_patch

    apply_patch()
