from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import User


class Command(BaseCommand):
    help = "Tek kurucu yöneticiyi atar: is_founder_admin=True; diğer kullanıcılarda bu bayrak kaldırılır."

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Kurucu yönetici kullanıcı adı")

    @transaction.atomic
    def handle(self, *args, **options):
        username = options["username"].strip()
        user = User.objects.select_for_update().filter(username=username).first()
        if not user:
            raise CommandError(f"Kullanıcı bulunamadı: {username}")
        User.objects.select_for_update().filter(is_founder_admin=True).exclude(pk=user.pk).update(is_founder_admin=False)
        user.is_founder_admin = True
        user.role = User.Role.ADMIN
        user.save(update_fields=["is_founder_admin", "role"])
        self.stdout.write(self.style.SUCCESS(f"Kurucu yönetici atandı: {username}"))
