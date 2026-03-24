from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403,F401

SECRET_KEY = env("DJANGO_SECRET_KEY")  # noqa: F405

DEBUG = False

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

_database_url = env("DATABASE_URL", default="").strip()  # noqa: F405
if not _database_url:
    raise ImproperlyConfigured("DATABASE_URL is required in production settings.")

DATABASES = {"default": env.db_url("DATABASE_URL", default=_database_url)}  # noqa: F405

INSTALLED_APPS = list(INSTALLED_APPS) + ["storages"]  # noqa: F405

# Boş bırakılırsa boto3 EC2 instance profile / varsayılan credential zincirini kullanır
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")  # noqa: F405
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")  # noqa: F405
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")  # noqa: F405
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")  # noqa: F405
AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default=None)  # noqa: F405
AWS_DEFAULT_ACL = None
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
AWS_QUERYSTRING_AUTH = False

if AWS_S3_CUSTOM_DOMAIN:
    AWS_S3_CUSTOM_DOMAIN = AWS_S3_CUSTOM_DOMAIN.strip()

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3boto3.S3StaticStorage",
    },
}

if AWS_S3_CUSTOM_DOMAIN:
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"
else:
    STATIC_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/static/"
    MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/media/"

STATICFILES_DIRS = []

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = env.bool("DJANGO_USE_X_FORWARDED_HOST", default=True)

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

EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")  # noqa: F405
