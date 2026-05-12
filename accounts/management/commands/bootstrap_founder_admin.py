"""
Bootstrap kurucu yönetici hesabı — yalnızca FOUNDER_ADMIN_EMAIL ortam
değişkeni ayarlıyken çalışır. Idempotent: hesap varsa günceller, yoksa oluşturur.

Render.com ücretsiz planda Shell bulunmadığından bu komut entrypoint.sh
içinden otomatik çağrılır. FOUNDER_ADMIN_EMAIL kaldırılınca bir daha çalışmaz.

Kullanım (Render env vars):
  FOUNDER_ADMIN_EMAIL    = ornek@mail.com   (zorunlu)
  FOUNDER_ADMIN_PASSWORD = gizlisifre       (zorunlu)
  FOUNDER_ADMIN_USERNAME = himmo            (isteğe bağlı; e-postadan türetilir)
"""

import os

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Env var'dan kurucu yönetici hesabı oluşturur veya günceller."

    @transaction.atomic
    def handle(self, *args, **options):
        from accounts.models import User

        email = (os.environ.get("FOUNDER_ADMIN_EMAIL") or "").strip()
        password = (os.environ.get("FOUNDER_ADMIN_PASSWORD") or "").strip()
        username_hint = (os.environ.get("FOUNDER_ADMIN_USERNAME") or "").strip()

        if not email:
            self.stdout.write("FOUNDER_ADMIN_EMAIL ayarli degil — atlanıyor.")
            return
        if not password:
            self.stderr.write(self.style.ERROR(
                "FOUNDER_ADMIN_PASSWORD ayarli degil — bootstrap iptal."
            ))
            return

        # Kullanıcı adı: env'den al, yoksa e-postadan türet
        if not username_hint:
            username_hint = email.split("@")[0].replace(".", "").lower() or "founder"

        # Mevcut hesabı e-posta ile ara
        user = User.objects.filter(email__iexact=email).first()
        created = False

        if user is None:
            # Kullanıcı adı çakışmasını önle
            username = username_hint
            suffix = 1
            while User.objects.filter(username=username).exists():
                username = f"{username_hint}{suffix}"
                suffix += 1
            user = User(username=username, email=email)
            created = True

        user.set_password(password)
        user.role = User.Role.ADMIN
        user.is_founder_admin = True
        user.is_active = True
        user.save()

        # Başka hiçbir kullanıcıda is_founder_admin kalmasın
        User.objects.filter(is_founder_admin=True).exclude(pk=user.pk).update(
            is_founder_admin=False
        )

        verb = "olusturuldu" if created else "guncellendi"
        self.stdout.write(self.style.SUCCESS(
            f"Kurucu yonetici {verb}: {user.username} <{user.email}>"
        ))
