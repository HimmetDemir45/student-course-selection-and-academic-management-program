"""
CI / GitHub Actions: MySQL-backed tests (no sqlite override).
Set DATABASE_URL to match the workflow service container.
"""

from .base import *  # noqa: F403,F401

# CI must set DJANGO_SECRET_KEY in the workflow; local fallbacks are non-production placeholders only.
SECRET_KEY = env("DJANGO_SECRET_KEY", default="ci-ephemeral-placeholder-not-for-production")  # noqa: F405
DEBUG = False

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = []

DATABASES = {
    "default": env.db_url(
        "DATABASE_URL",
        default="mysql://root:root@127.0.0.1:3306/github_actions",
    )
}  # noqa: F405

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

RATELIMIT_ENABLE = False

# core/urls.py test rotalari: CI DEBUG=False oldugundan True (prod'da tanimlanmaz).
# Rollback: bu satiri silin; test URL'leri icin core/urls.py'deki kosulu DEBUG=True yapin veya kaldirin.
INCLUDE_CORE_DEV_TEST_ROUTES = True
