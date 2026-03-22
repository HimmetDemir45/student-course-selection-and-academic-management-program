import sys

from .base import *  # noqa: F403,F401

DEBUG = True

if "test" in sys.argv:
    DATABASES["default"] = {  # noqa: F405
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Password reset e-postalari gelistirme ortaminda terminale duser.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
