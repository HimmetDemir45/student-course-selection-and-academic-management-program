"""
Aktif dönemi bugünün tarihine göre ayarlar. Diğer tüm dönemleri pasifleştirir.

Kullanım:
    python manage.py set_active_semester              # bugünün tarihine göre
    python manage.py set_active_semester --year 2025-2026 --term spring
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from academic.models import Semester


class Command(BaseCommand):
    help = "Aktif dönemi belirler; diğer tüm dönemleri pasifleştirir."

    def add_arguments(self, parser):
        parser.add_argument("--year", help="Akademik yıl (örn: 2025-2026)")
        parser.add_argument(
            "--term",
            choices=["fall", "spring", "summer"],
            help="Dönem (fall|spring|summer)",
        )

    def handle(self, *args, **opts):
        year = opts.get("year")
        term = opts.get("term")

        target = None
        if year and term:
            try:
                target = Semester.objects.get(academic_year=year, term=term)
            except Semester.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f"Semester bulunamadı: {year} {term}"
                ))
                return
        else:
            today = timezone.localdate()
            for s in Semester.objects.all():
                if s.start_date <= today <= s.end_date:
                    target = s
                    break
            if target is None:
                self.stdout.write(self.style.ERROR(
                    f"Bugün ({today}) hiçbir dönemin tarih aralığına düşmüyor. "
                    "--year ve --term ile manuel seçim yapın."
                ))
                return

        Semester.objects.exclude(pk=target.pk).update(is_active=False)
        if not target.is_active:
            target.is_active = True
            target.save(update_fields=["is_active"])

        self.stdout.write(self.style.SUCCESS(
            f"Aktif dönem: {target} ({target.start_date} → {target.end_date})"
        ))
        passive = Semester.objects.exclude(pk=target.pk).count()
        self.stdout.write(f"Pasifleştirilen dönem sayısı: {passive}")
