from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    LOG_LEVEL=(str, "INFO"),
    LOG_SERVICE_NAME=(str, "student-academic-mgmt"),
)
environ.Env.read_env(BASE_DIR / ".env")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "core",
    "students",
    "instructors",
    "courses",
    "enrollments",
    "academic",
    "dashboard",
    "audit_logs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.content_security_policy.ContentSecurityPolicyMiddleware",
    "core.middleware.request_id.RequestIdMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "core.middleware.login_throttle.LoginBruteForceMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.navigation",
                "core.context_processors.landing_stats",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database: DATABASE_URL (e.g. mysql://user:pass@host:port/db) or discrete DB_* vars
if env("DATABASE_URL", default=None):
    DATABASES = {"default": env.db_url("DATABASE_URL")}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env("DB_NAME", default="university_db"),
            "USER": env("DB_USER", default="root"),
            "PASSWORD": env("DB_PASSWORD", default=""),
            "HOST": env("DB_HOST", default="127.0.0.1"),
            "PORT": env("DB_PORT", default="3306"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "tr"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ("tr", "Türkçe"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "phase4-cache",
    }
}

AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "core:home"

LOGIN_THROTTLE_MAX_FAILURES = 5
LOGIN_THROTTLE_LOCKOUT_SECONDS = 900

SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

LOG_LEVEL = env("LOG_LEVEL")
LOG_SERVICE_NAME = env("LOG_SERVICE_NAME")

# Production JSON logs (structlog + CloudWatch/Loki/ELK). See docs/observability.md
DJANGO_LOG_JSON = env.bool("DJANGO_LOG_JSON", default=False)

FEATURE_FLAGS = {
    "enrollment_ratelimit": env.bool("FEATURE_ENROLLMENT_RATELIMIT", default=True),
}

RATELIMIT_ENABLE = env.bool("RATELIMIT_ENABLE", default=True)

if DJANGO_LOG_JSON:
    from core.structlog_config import get_json_logging_dict, init_structlog_for_json_logging

    LOGGING = get_json_logging_dict(LOG_LEVEL)
    init_structlog_for_json_logging()
else:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "()": "core.logging_utils.RedactingFormatter",
                "format": "{levelname} {asctime} {name} service={service} request_id={request_id} {message}",
                "style": "{",
            },
        },
        "filters": {
            "request_context": {
                "()": "core.request_context.RequestContextFilter",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "verbose",
                "filters": ["request_context"],
            },
        },
        "root": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
        },
        "loggers": {
            "django": {
                "handlers": ["console"],
                "level": LOG_LEVEL,
                "propagate": False,
            },
            "django.request": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "request": {
                "handlers": ["console"],
                "level": LOG_LEVEL,
                "propagate": False,
            },
        },
    }
