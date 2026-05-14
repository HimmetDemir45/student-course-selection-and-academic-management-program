"""
Danışman hocaları ayarlar:
  - İbrahim Uğur YILMAZ  → is_advisor=True  (seed_yzm_weekly ile zaten oluştu)
  - Musa ARSLAN           → oluştur + is_advisor=True
  - Diğer tüm hocalar    → is_advisor=False  (güvenlik için sıfırla)

Kullanım:
    python manage.py seed_danishman
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from instructors.models import InstructorProfile


DANISMANLAR = [
    {
        "username": "inst_ibrahim_ugur_yilmaz",
        "first_name": "İbrahim Uğur",
        "last_name": "YILMAZ",
        "title": "Öğr.Gör.",
        "employee_no_hint": "YILMAZ_IU",
    },
    {
        "username": "inst_musa_arslan",
        "first_name": "Musa",
        "last_name": "ARSLAN",
        "title": "Dr.Öğr.Üyesi",
        "employee_no_hint": "ARSLAN_M",
    },
]


class Command(BaseCommand):
    help = "Danışman yetkilerini ayarlar (Musa Arslan + İbrahim Uğur Yılmaz)."

    @transaction.atomic
    def handle(self, *args, **opts):
        from academic.models import Department

        yzm_dept = Department.objects.filter(code="YZM").first()

        # Önce tüm hocaların is_advisor'ını False yap
        updated = InstructorProfile.objects.update(is_advisor=False)
        self.stdout.write(f"  {updated} hocanın is_advisor=False yapıldı.")

        for data in DANISMANLAR:
            user, u_created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "email": f"{data['username']}@uni.edu.tr",
                    "role": User.Role.INSTRUCTOR,
                },
            )
            if u_created or not user.has_usable_password():
                user.set_password("DemoPass2026!")
                user.save()

            employee_no = f"ADV{abs(hash(data['employee_no_hint'])) % 10**6:06d}"
            profile, p_created = InstructorProfile.objects.get_or_create(
                user=user,
                defaults={
                    "department": yzm_dept,
                    "title": data["title"],
                    "is_approved": True,
                    "is_advisor": True,
                    "employee_no": employee_no,
                },
            )
            if not profile.is_advisor or not profile.is_approved:
                profile.is_advisor = True
                profile.is_approved = True
                profile.save(update_fields=["is_advisor", "is_approved"])

            tag = "YENI" if p_created else "OK  "
            self.stdout.write(
                f"  {tag} Danışman: {user.get_full_name()} "
                f"({user.username}) is_advisor={profile.is_advisor}"
            )

        self.stdout.write(self.style.SUCCESS("\n[OK] Danışman atamaları tamamlandı."))
