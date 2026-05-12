import django.utils.translation
from django.db import migrations, models


class Migration(migrations.Migration):
    """State-only: sync role choices (English→Turkish) and is_founder_admin help_text (plain→gettext_lazy)."""

    dependencies = [
        ("accounts", "0002_phase11_founder_adminrequest"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("admin", django.utils.translation.gettext_lazy("Yönetici")),
                    ("student", django.utils.translation.gettext_lazy("Öğrenci")),
                    ("instructor", django.utils.translation.gettext_lazy("Öğretim üyesi")),
                ],
                default="student",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="is_founder_admin",
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text=django.utils.translation.gettext_lazy(
                    "Kurucu yönetici: tek hesap; yalnızca bu kullanıcı admin taleplerini onaylayabilir."
                ),
            ),
        ),
        migrations.AlterField(
            model_name="adminrequest",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", django.utils.translation.gettext_lazy("Beklemede")),
                    ("approved", django.utils.translation.gettext_lazy("Onaylandı")),
                    ("rejected", django.utils.translation.gettext_lazy("Reddedildi")),
                ],
                db_index=True,
                default="pending",
                max_length=20,
            ),
        ),
    ]
