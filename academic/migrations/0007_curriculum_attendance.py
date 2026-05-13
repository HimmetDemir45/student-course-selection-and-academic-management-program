import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academic', '0006_metadata_help_texts'),
        ('courses', '0002_course_type_field'),
        ('instructors', '0003_add_is_approved'),
        ('students', '0003_add_is_approved'),
    ]

    operations = [
        # ── CurriculumItem ────────────────────────────────────────────
        migrations.CreateModel(
            name='CurriculumItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('year_level', models.PositiveSmallIntegerField(
                    help_text='Kaçıncı yılda alınmalı (1–4).',
                )),
                ('term', models.CharField(
                    choices=[
                        ('fall', 'Güz'),
                        ('spring', 'Bahar'),
                        ('summer', 'Yaz'),
                    ],
                    max_length=10,
                )),
                ('order', models.PositiveSmallIntegerField(
                    default=0,
                    help_text='Aynı dönem içindeki görüntüleme sırası.',
                )),
                ('program', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='curriculum_items',
                    to='academic.program',
                )),
                ('course', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='curriculum_items',
                    to='courses.course',
                )),
            ],
            options={
                'ordering': ('year_level', 'term', 'order', 'course__code'),
            },
        ),
        migrations.AddConstraint(
            model_name='curriculumitem',
            constraint=models.UniqueConstraint(
                fields=('program', 'course'),
                name='uniq_curriculum_program_course',
            ),
        ),

        # ── AttendanceRecord ──────────────────────────────────────────
        migrations.CreateModel(
            name='AttendanceRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('date', models.DateField(db_index=True)),
                ('section', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attendance_records',
                    to='academic.coursesection',
                )),
                ('taken_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='attendance_records',
                    to='instructors.instructorprofile',
                )),
            ],
            options={
                'ordering': ('-date',),
            },
        ),
        migrations.AddConstraint(
            model_name='attendancerecord',
            constraint=models.UniqueConstraint(
                fields=('section', 'date'),
                name='uniq_attendance_section_date',
            ),
        ),

        # ── AttendanceEntry ───────────────────────────────────────────
        migrations.CreateModel(
            name='AttendanceEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(
                    choices=[
                        ('present', 'Geldi'),
                        ('absent', 'Gelmedi'),
                        ('excused', 'Mazeretli'),
                        ('late', 'Geç geldi'),
                    ],
                    db_index=True,
                    default='present',
                    max_length=10,
                )),
                ('note', models.TextField(blank=True)),
                ('record', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='entries',
                    to='academic.attendancerecord',
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attendance_entries',
                    to='students.studentprofile',
                )),
            ],
            options={
                'ordering': ('student__student_no',),
            },
        ),
        migrations.AddConstraint(
            model_name='attendanceentry',
            constraint=models.UniqueConstraint(
                fields=('record', 'student'),
                name='uniq_attendance_entry',
            ),
        ),
    ]
