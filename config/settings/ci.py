"""
CI / GitHub Actions: MySQL-backed tests (no sqlite override).
Set DATABASE_URL to match the workflow service container.
"""

from .base import *  # noqa: F403,F401

SECRET_KEY = "ci-not-a-secret-key-do-not-use-in-production"  # noqa: F405
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
