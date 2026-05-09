from django.db import migrations
from django.utils import timezone


def forwards(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    StudentProfile = apps.get_model("students", "StudentProfile")
    year = timezone.now().year
    for user in User.objects.filter(role="student").iterator():
        if StudentProfile.objects.filter(user_id=user.pk).exists():
            continue
        core = str(user.pk)
        candidate = f"S{core}"
        if len(candidate) > 20:
            candidate = core[-20:]
        n = 0
        while StudentProfile.objects.filter(student_no=candidate).exists():
            n += 1
            tail = f"-{n}"
            trimmed = f"S{core}"
            if len(trimmed) + len(tail) > 20:
                trimmed = trimmed[: max(1, 20 - len(tail))]
            candidate = (trimmed + tail)[:20]
        StudentProfile.objects.create(
            user_id=user.pk,
            student_no=candidate,
            enrollment_year=year,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("students", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
