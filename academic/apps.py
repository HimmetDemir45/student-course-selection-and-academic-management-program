"""
`academic` uygulamasının yapılandırması.
"""
from django.apps import AppConfig


class AcademicConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "academic"

    def ready(self):
        from . import signals  # noqa: F401
