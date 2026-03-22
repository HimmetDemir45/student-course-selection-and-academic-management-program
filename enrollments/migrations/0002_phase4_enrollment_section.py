import django.db.models.deletion
from django.db import migrations, models


def forwards_fill_section(apps, schema_editor):
    CourseOffering = apps.get_model("courses", "CourseOffering")
    CourseSection = apps.get_model("academic", "CourseSection")
    Enrollment = apps.get_model("enrollments", "Enrollment")
    for off in CourseOffering.objects.all():
        CourseSection.objects.get_or_create(
            offering_id=off.pk,
            defaults={"is_active": off.is_active},
        )
    for e in Enrollment.objects.all():
        sec = CourseSection.objects.get(offering_id=e.offering_id)
        e.section_id = sec.pk
        e.save(update_fields=["section_id"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("academic", "0003_phase4_section_semester"),
        ("enrollments", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="enrollment",
            name="section",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="enrollments",
                to="academic.coursesection",
            ),
        ),
        migrations.RunPython(forwards_fill_section, noop_reverse),
        migrations.RemoveConstraint(
            model_name="enrollment",
            name="uniq_enrollment_student_offering",
        ),
        migrations.RemoveField(
            model_name="enrollment",
            name="offering",
        ),
        migrations.AlterField(
            model_name="enrollment",
            name="section",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="enrollments",
                to="academic.coursesection",
            ),
        ),
        migrations.AlterField(
            model_name="enrollment",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("enrolled", "Enrolled"),
                    ("dropped", "Dropped"),
                    ("withdrawn", "Withdrawn"),
                    ("completed", "Completed"),
                ],
                db_index=True,
                default="enrolled",
                max_length=20,
            ),
        ),
        migrations.AddConstraint(
            model_name="enrollment",
            constraint=models.UniqueConstraint(
                fields=("student", "section"),
                name="uniq_enrollment_student_section",
            ),
        ),
    ]
