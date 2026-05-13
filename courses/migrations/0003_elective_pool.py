from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academic', '0002_initial'),
        ('courses', '0002_course_type_field'),
    ]

    operations = [
        migrations.CreateModel(
            name='ElectivePool',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('name', models.CharField(db_index=True, max_length=150)),
                ('description', models.TextField(blank=True, help_text='Öğrencilere gösterilecek açıklama.')),
                ('required_count', models.PositiveSmallIntegerField(default=1, help_text='Öğrencinin bu havuzdan seçmesi gereken ders sayısı.')),
                ('program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='elective_pools', to='academic.program')),
                ('courses', models.ManyToManyField(blank=True, related_name='elective_pools', to='courses.course')),
            ],
            options={
                'ordering': ('program__code', 'name'),
            },
        ),
        migrations.AddConstraint(
            model_name='electivepool',
            constraint=models.UniqueConstraint(fields=('program', 'name'), name='uniq_elective_pool_program_name'),
        ),
    ]
