"""
Enrollment post_save signal:
Bir kayıt DROPPED olduğunda aynı şubede bekleyen ilk WAITLISTED öğrenciyi
PENDING'e alır (queryset.update ile full_clean bypass).
"""
from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender="enrollments.Enrollment")
def promote_waitlisted_on_drop(sender, instance, created, **kwargs):
    if created or instance.status != "dropped":
        return

    from enrollments.models import Enrollment

    waitlisted_qs = Enrollment.objects.filter(
        section_id=instance.section_id,
        status=Enrollment.Status.WAITLISTED,
    ).order_by("created_at")

    first = waitlisted_qs.first()
    if first:
        Enrollment.objects.filter(pk=first.pk).update(status=Enrollment.Status.PENDING)
