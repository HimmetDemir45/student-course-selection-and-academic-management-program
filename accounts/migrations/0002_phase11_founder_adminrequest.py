# Generated manually for Phase 11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_founder_admin",
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text="Kurucu yönetici: tek hesap; yalnızca bu kullanıcı admin taleplerini onaylayabilir.",
            ),
        ),
        migrations.CreateModel(
            name="AdminRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "Beklemede"), ("approved", "Onaylandı"), ("rejected", "Reddedildi")], db_index=True, default="pending", max_length=20)),
                ("reason", models.TextField(blank=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviewed_admin_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="admin_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddIndex(
            model_name="adminrequest",
            index=models.Index(fields=["status", "created_at"], name="idx_adminreq_status_created"),
        ),
    ]
