"""
Danışman atamaları:
  - SADECE İbrahim Uğur YILMAZ danışman olacak (is_advisor=True)
  - Diğer tüm hocalar is_advisor=False
  - TÜM YZM öğrencilerinin advisor'ı İbrahim Uğur YILMAZ'a atanır
  - İ.U.Yılmaz hem öğretim üyesi hem danışman olacak

Kullanım:
    python manage.py seed_danishman
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from instructors.models import InstructorProfile


ADVISOR_USERNAME = "inst_ibrahim_yilmaz"  # seed_yzm_weekly._instructor_username() ile aynı format: inst_<ilk_ad>_<soyad>
ADVISOR_FIRST_NAME = "İbrahim Uğur"
ADVISOR_LAST_NAME = "YILMAZ"
ADVISOR_TITLE = "Öğr.Gör."
LEGACY_USERNAMES = ("inst_ibrahim_ugur_yilmaz",)  # Eski hatalı kullanıcı adları — varsa silinir/birleştirilir


class Command(BaseCommand):
    help = "Danışman yetkisini SADECE İbrahim Uğur Yılmaz'a verir ve tüm YZM öğrencilerini ona atar."

    @transaction.atomic
    def handle(self, *args, **opts):
        from academic.models import Department
        from students.models import StudentProfile

        yzm_dept = Department.objects.filter(code="YZM").first()
        if yzm_dept is None:
            self.stdout.write(self.style.ERROR(
                "[HATA] YZM bölümü bulunamadı. Önce 'seed_yzm_weekly' çalıştırın."
            ))
            return

        # 0) Geriye dönük temizlik: yanlış username'le açılmış eski İ.U.Yılmaz hesaplarını sil
        #    (öğrenci/öğretim verisi yoksa). Bu, seed_yzm_weekly ile seed_danishman
        #    arasındaki username uyumsuzluğundan kaynaklanan duplicate kullanıcıları kaldırır.
        for legacy in LEGACY_USERNAMES:
            legacy_user = User.objects.filter(username=legacy).first()
            if not legacy_user:
                continue
            legacy_profile = InstructorProfile.objects.filter(user=legacy_user).first()
            has_offerings = legacy_profile is not None and legacy_profile.offerings.exists()
            if not has_offerings:
                # Profili silmeden önce danışan referanslarını temizle (advisor → NULL)
                from students.models import StudentProfile
                if legacy_profile is not None:
                    StudentProfile.objects.filter(advisor=legacy_profile).update(advisor=None)
                    legacy_profile.delete()
                legacy_user.delete()
                self.stdout.write(f"  [TEMIZLIK] Eski duplicate hesap silindi: {legacy}")

        # 1) Tüm hocaları danışmanlıktan al
        reset = InstructorProfile.objects.update(is_advisor=False)
        self.stdout.write(f"  {reset} hocanın is_advisor=False yapıldı.")

        # 2) İbrahim Uğur YILMAZ kullanıcısı + profili
        user, u_created = User.objects.get_or_create(
            username=ADVISOR_USERNAME,
            defaults={
                "first_name": ADVISOR_FIRST_NAME,
                "last_name": ADVISOR_LAST_NAME,
                "email": f"{ADVISOR_USERNAME}@uni.edu.tr",
                "role": User.Role.INSTRUCTOR,
            },
        )
        if u_created or not user.has_usable_password():
            user.set_password("DemoPass2026!")
            user.save()

        employee_no = f"ADV{abs(hash(ADVISOR_USERNAME)) % 10**6:06d}"
        profile, p_created = InstructorProfile.objects.get_or_create(
            user=user,
            defaults={
                "department": yzm_dept,
                "title": ADVISOR_TITLE,
                "is_approved": True,
                "is_advisor": True,
                "employee_no": employee_no,
            },
        )
        # Mevcut profili tek danışman yapacak şekilde güncelle
        update_fields = []
        if not profile.is_advisor:
            profile.is_advisor = True
            update_fields.append("is_advisor")
        if not profile.is_approved:
            profile.is_approved = True
            update_fields.append("is_approved")
        if profile.department_id != yzm_dept.pk:
            profile.department = yzm_dept
            update_fields.append("department")
        if update_fields:
            profile.save(update_fields=update_fields)

        tag = "YENI" if p_created else "OK  "
        self.stdout.write(
            f"  {tag} Tek danışman: {user.get_full_name()} "
            f"({user.username}) is_advisor={profile.is_advisor}"
        )

        # 3) Tüm YZM öğrencilerinin advisor'ını bu profile ata
        # (department=YZM veya program.department=YZM olanlar)
        from django.db.models import Q
        yzm_students = StudentProfile.objects.filter(
            Q(department=yzm_dept) | Q(program__department=yzm_dept)
        )
        assigned = yzm_students.update(advisor=profile)
        self.stdout.write(
            f"  {assigned} YZM öğrencisinin danışmanı '{user.get_full_name()}' olarak atandı."
        )

        self.stdout.write(self.style.SUCCESS(
            "\n[OK] Danışman atamaları tamamlandı. "
            "Artık SADECE İbrahim Uğur Yılmaz YZM öğrencilerinin ders kayıtlarını onaylayabilir."
        ))
