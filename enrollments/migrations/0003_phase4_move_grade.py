from django.db import migrations


def copy_grades_to_academic(apps, schema_editor):
    OldGrade = apps.get_model("enrollments", "Grade")
    NewGrade = apps.get_model("academic", "Grade")
    for og in OldGrade.objects.all():
        NewGrade.objects.create(
            enrollment_id=og.enrollment_id,
            letter_grade=og.letter_grade,
            numeric_grade=og.numeric_grade,
            created_at=og.created_at,
            updated_at=og.updated_at,
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("enrollments", "0002_phase4_enrollment_section"),
        ("academic", "0004_phase4_grade"),
    ]

    operations = [
        migrations.RunPython(copy_grades_to_academic, noop_reverse),
        migrations.DeleteModel(
            name="Grade",
        ),
    ]
