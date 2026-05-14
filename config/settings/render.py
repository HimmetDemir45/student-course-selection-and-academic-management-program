"""Render.com deployment settings — uses WhiteNoise for static files (no S3 required)."""

from .base import *  # noqa: F403,F401

SECRET_KEY = env("DJANGO_SECRET_KEY")  # noqa: F405

DEBUG = False

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")  # noqa: F405

CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405

# WhiteNoise: SecurityMiddleware'den hemen sonra gelmeli
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],  # noqa: F405
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Manifest'te kayıt yoksa 500 fırlatmak yerine orijinal URL döner
WHITENOISE_MANIFEST_STRICT = False

STATIC_URL = "/static/"

# Veritabanı bağlantısını worker ömrü boyunca canlı tut (Render'da faydalı)
CONN_MAX_AGE = 60

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = env.bool("DJANGO_USE_X_FORWARDED_HOST", default=True)  # noqa: F405

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

# ── E-posta gönderimi ─────────────────────────────────────────────────────
# Render'da gerçek e-posta göndermek için EMAIL_HOST_USER ortam değişkeni
# tanımlanmalıdır. Tanımlı değilse console backend'e düşer (log'a yazar,
# gerçekten göndermez) — geliştirme/test için güvenli varsayılan.
_EMAIL_USER = env("EMAIL_HOST_USER", default="")  # noqa: F405
EMAIL_BACKEND = env(  # noqa: F405
    "EMAIL_BACKEND",
    default=(
        "django.core.mail.backends.smtp.EmailBackend"
        if _EMAIL_USER
        else "django.core.mail.backends.console.EmailBackend"
    ),
)
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")  # noqa: F405
EMAIL_PORT = env.int("EMAIL_PORT", default=587)  # noqa: F405
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)  # noqa: F405
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)  # noqa: F405
EMAIL_HOST_USER = _EMAIL_USER
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")  # noqa: F405
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=15)  # noqa: F405
DEFAULT_FROM_EMAIL = env(  # noqa: F405
    "DEFAULT_FROM_EMAIL",
    default=_EMAIL_USER or "webmaster@localhost",
)
SERVER_EMAIL = env("SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)  # noqa: F405
