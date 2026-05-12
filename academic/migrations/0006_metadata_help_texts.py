from django.db import migrations, models


class Migration(migrations.Migration):
    """State-only: adds help_text to fields that were migrated without it."""

    dependencies = [
        ("academic", "0005_phase6_perf_indexes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="semester",
            name="add_drop_start",
            field=models.DateField(
                blank=True,
                null=True,
                help_text="Bos birakilirsa ekle-birak kontrolu gevsetilir (gelistirme uyumu).",
            ),
        ),
        migrations.AlterField(
            model_name="coursesection",
            name="max_enrollment",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                help_text="Bos ise CourseOffering.quota gecerlidir.",
            ),
        ),
    ]
