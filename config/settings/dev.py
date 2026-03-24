import sys

from .base import *  # noqa: F403,F401

SECRET_KEY = env(  # noqa: F405
    "DJANGO_SECRET_KEY",
    default=env("SECRET_KEY", default="django-insecure-dev-only-change-me"),  # noqa: F405
)

DEBUG = env.bool("DJANGO_DEBUG", default=env.bool("DEBUG", default=True))  # noqa: F405

ALLOWED_HOSTS = env.list(  # noqa: F405
    "DJANGO_ALLOWED_HOSTS",
    default=env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"]),
)

CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

if "test" in sys.argv:
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

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
