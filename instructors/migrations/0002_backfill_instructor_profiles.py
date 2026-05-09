from django.db import migrations


def forwards(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    InstructorProfile = apps.get_model("instructors", "InstructorProfile")
    for user in User.objects.filter(role="instructor").iterator():
        if InstructorProfile.objects.filter(user_id=user.pk).exists():
            continue
        core = str(user.pk)
        candidate = f"E{core}"
        if len(candidate) > 20:
            candidate = core[-20:]
        n = 0
        while InstructorProfile.objects.filter(employee_no=candidate).exists():
            n += 1
            tail = f"-{n}"
            trimmed = f"E{core}"
            if len(trimmed) + len(tail) > 20:
                trimmed = trimmed[: max(1, 20 - len(tail))]
            candidate = (trimmed + tail)[:20]
        InstructorProfile.objects.create(user_id=user.pk, employee_no=candidate)


class Migration(migrations.Migration):
    dependencies = [
        ("instructors", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
