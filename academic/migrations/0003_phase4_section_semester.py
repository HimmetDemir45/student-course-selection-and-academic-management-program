import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0001_initial"),
        ("academic", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="semester",
            name="add_drop_start",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="semester",
            name="add_drop_end",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="CourseSection",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("max_enrollment", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "offering",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="section_detail",
                        to="courses.courseoffering",
                    ),
                ),
            ],
            options={
                "ordering": ("offering__course__code", "offering__section"),
            },
        ),
        migrations.CreateModel(
            name="SectionTimeSlot",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "weekday",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (0, "Pazartesi"),
                            (1, "Sali"),
                            (2, "Carsamba"),
                            (3, "Persembe"),
                            (4, "Cuma"),
                            (5, "Cumartesi"),
                            (6, "Pazar"),
                        ]
                    ),
                ),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                (
                    "section",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="time_slots",
                        to="academic.coursesection",
                    ),
                ),
            ],
            options={
                "ordering": ("section_id", "weekday", "start_time"),
            },
        ),
    ]
