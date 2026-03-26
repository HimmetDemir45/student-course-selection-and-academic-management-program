import os
import random
from decimal import getcontext

import pytest
from django.core.cache import cache
from freezegun import freeze_time


@pytest.fixture(scope="session", autouse=True)
def deterministic_seed():
    os.environ.setdefault("PYTHONHASHSEED", "42")
    random.seed(42)
    getcontext().prec = 8


@pytest.fixture(autouse=True)
def stable_time():
    with freeze_time("2026-03-26 10:00:00", tz_offset=3):
        yield


@pytest.fixture(autouse=True)
def safe_test_settings(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "phase9-tests",
        }
    }
    settings.PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]
    settings.SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
    settings.RATELIMIT_ENABLE = True
    yield


@pytest.fixture(autouse=True)
def clear_cache_between_tests():
    cache.clear()
    yield
    cache.clear()
