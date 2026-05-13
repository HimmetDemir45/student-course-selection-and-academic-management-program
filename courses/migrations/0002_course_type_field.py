from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='course_type',
            field=models.CharField(
                choices=[
                    ('mandatory', 'Zorunlu'),
                    ('elective', 'Seçmeli'),
                    ('free_elective', 'Serbest Seçmeli'),
                ],
                db_index=True,
                default='mandatory',
                max_length=20,
            ),
        ),
    ]
