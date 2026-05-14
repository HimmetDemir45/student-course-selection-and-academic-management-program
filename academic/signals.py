"""
Akademik modeller için post_save/post_delete signal handler'ları (cache invalidation, audit kayıtları).
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from courses.models import CourseOffering


@receiver(post_save, sender=CourseOffering)
def ensure_course_section(sender, instance, **kwargs):
    from academic.models import CourseSection

    CourseSection.objects.get_or_create(
        offering=instance,
        defaults={"is_active": instance.is_active},
    )
