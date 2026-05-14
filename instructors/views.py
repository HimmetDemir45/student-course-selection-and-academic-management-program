"""
Akademisyen view'ları: profil sayfası, admin tarafından akademisyen yönetimi.
"""
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import ListView, UpdateView

from core.breadcrumbs import home, items
from core.permissions import AdminRequiredMixin, InstructorRequiredMixin

from .forms import InstructorAssignForm
from .models import InstructorProfile


class InstructorHomeView(InstructorRequiredMixin, View):
    template_name = "instructors/index.html"

    def get(self, request):
        from courses.models import CourseOffering
        from enrollments.models import Enrollment

        try:
            profile = request.user.instructor_profile
        except ObjectDoesNotExist:
            profile = None

        offering_count = 0
        pending_grades = 0
        pending_advisees = 0

        if profile:
            offering_count = CourseOffering.objects.filter(
                instructor=profile, is_active=True
            ).count()
            pending_grades = (
                Enrollment.objects.filter(
                    section__offering__instructor=profile,
                    status=Enrollment.Status.ENROLLED,
                )
                .filter(Q(academic_grade__isnull=True) | Q(academic_grade__letter_grade=""))
                .count()
            )
            pending_advisees = Enrollment.objects.filter(
                student__advisor=profile,
                status=Enrollment.Status.PENDING,
            ).count()

        return render(request, self.template_name, {
            "profile": profile,
            "offering_count": offering_count,
            "pending_grades": pending_grades,
            "pending_advisees": pending_advisees,
        })


class InstructorAdminListView(AdminRequiredMixin, ListView):
    model = InstructorProfile
    template_name = "instructors/admin_list.html"
    context_object_name = "instructors"
    paginate_by = 30

    def get_queryset(self):
        qs = InstructorProfile.objects.select_related("user", "department")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(employee_no__icontains=q)
                | Q(user__first_name__icontains=q)
                | Q(user__last_name__icontains=q)
                | Q(user__username__icontains=q)
            )
        dept = (self.request.GET.get("dept") or "").strip()
        if dept.isdigit():
            qs = qs.filter(department_id=int(dept))
        approved = self.request.GET.get("approved", "")
        if approved == "1":
            qs = qs.filter(is_approved=True)
        elif approved == "0":
            qs = qs.filter(is_approved=False)
        return qs.order_by("employee_no")

    def get_context_data(self, **kwargs):
        from academic.models import Department
        ctx = super().get_context_data(**kwargs)
        ctx["current_filters"] = {
            "q": self.request.GET.get("q", "").strip(),
            "dept": self.request.GET.get("dept", ""),
            "approved": self.request.GET.get("approved", ""),
        }
        ctx["departments"] = Department.objects.filter(is_active=True).order_by("code")
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Akademisyen yönetimi"), "url": None},
        )
        return ctx


class InstructorAdminEditView(AdminRequiredMixin, UpdateView):
    model = InstructorProfile
    form_class = InstructorAssignForm
    template_name = "instructors/admin_form.html"
    success_url = reverse_lazy("instructors:admin_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            _("%(no)s sicil numaralı akademisyenin bilgileri güncellendi.") % {
                "no": self.object.employee_no
            },
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Akademisyen yönetimi"), "url": reverse("instructors:admin_list")},
            {"label": _("Düzenle"), "url": None},
        )
        return ctx


class InstructorEnrollmentReviewView(InstructorRequiredMixin, View):
    """
    Eğitim görevlisinin kendisinin öğrettiği derslere kayıtlı öğrencileri görmesi.
    """
    template_name = "instructors/enrollment_review.html"

    def get(self, request):
        from courses.models import CourseOffering
        from enrollments.models import Enrollment
        from django.utils import timezone

        try:
            profile = request.user.instructor_profile
        except ObjectDoesNotExist:
            return render(request, self.template_name, {"error": _("Akademisyen profili bulunamadı.")})

        # Aktif dönemdeki kendi dersleri
        today = timezone.localdate()
        from academic.models import Semester
        active_semester = Semester.objects.filter(
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        ).first()

        offerings = CourseOffering.objects.filter(
            instructor=profile,
            is_active=True
        )

        if active_semester:
            offerings = offerings.filter(semester=active_semester)

        # Her ders için enrollmentları topla
        courses_with_enrollments = []
        for offering in offerings:
            section = offering.section_detail
            enrollments = Enrollment.objects.filter(
                section=section
            ).select_related("student__user")

            courses_with_enrollments.append({
                "offering": offering,
                "enrollments": enrollments,
                "total": enrollments.count(),
                "pending_review": enrollments.filter(instructor_approved=False).count(),
            })

        ctx = {
            "courses_with_enrollments": courses_with_enrollments,
            "active_semester": active_semester,
            "breadcrumb_items": items(
                home(),
                {"label": _("Ders İncelemesi"), "url": None},
            ),
        }
        return render(request, self.template_name, ctx)


class InstructorApproveEnrollmentView(InstructorRequiredMixin, View):
    """
    Eğitim görevlisinin bir öğrencinin ders seçimini onaylaması.
    """

    def post(self, request, enrollment_id):
        from enrollments.models import Enrollment
        from django.http import JsonResponse
        from django.shortcuts import get_object_or_404
        from audit_logs.services import log_event

        try:
            profile = request.user.instructor_profile
        except ObjectDoesNotExist:
            return JsonResponse({"error": _("Akademisyen profili bulunamadı.")}, status=403)

        enrollment = get_object_or_404(Enrollment, pk=enrollment_id)

        # Yetki kontrolü: Bu öğrencinin dersi benim dersim mi?
        if enrollment.section.offering.instructor != profile:
            return JsonResponse({"error": _("Yetkiniz yok.")}, status=403)

        # Onay yap
        enrollment.instructor_approved = True
        enrollment.instructor_approved_by = profile
        enrollment.instructor_approved_at = timezone.localtime()
        enrollment.save()

        log_event(
            event_type="enrollment.instructor_approved",
            actor=request.user,
            target_type="enrollments.Enrollment",
            target_id=str(enrollment.pk),
            metadata={
                "student": str(enrollment.student),
                "course": str(enrollment.section.offering.course),
            },
            request=request,
        )

        messages.success(request, _("Enrollment approved successfully."))
        return JsonResponse({"success": True})


class InstructorGradeListView(InstructorRequiredMixin, View):
    """
    Eğitim görevlisinin derslerinde kaydolan öğrencileri ve notlarını görmesi.
    """
    template_name = "instructors/grade_list.html"

    def get(self, request):
        from courses.models import CourseOffering
        from enrollments.models import Enrollment
        from academic.models import Grade

        try:
            profile = request.user.instructor_profile
        except ObjectDoesNotExist:
            return render(request, self.template_name, {"error": _("Akademisyen profili bulunamadı.")})

        # Aktif dersleri bul
        offerings = CourseOffering.objects.filter(
            instructor=profile,
            is_active=True
        ).select_related("course", "semester")

        # Her ders için öğrenci notları
        courses_with_grades = []
        for offering in offerings:
            section = offering.section_detail
            enrollments = Enrollment.objects.filter(
                section=section,
                status=Enrollment.Status.ENROLLED
            ).select_related("student__user", "academic_grade")

            grades_data = []
            for enrollment in enrollments:
                grade = Grade.objects.filter(enrollment=enrollment).first()
                grades_data.append({
                    "enrollment": enrollment,
                    "grade": grade,
                })

            courses_with_grades.append({
                "offering": offering,
                "grades": grades_data,
                "total": enrollments.count(),
                "graded": sum(1 for g in grades_data if g["grade"] and g["grade"].letter_grade),
            })

        ctx = {
            "courses_with_grades": courses_with_grades,
            "breadcrumb_items": items(
                home(),
                {"label": _("Not Girişi"), "url": None},
            ),
        }
        return render(request, self.template_name, ctx)


class InstructorGradeEntryView(InstructorRequiredMixin, View):
    """
    Eğitim görevlisinin öğrenci notlarını girmesi.
    """
    template_name = "instructors/grade_entry.html"

    def get(self, request, section_id):
        from academic.models import CourseSection
        from enrollments.models import Enrollment
        from django.shortcuts import get_object_or_404

        try:
            profile = request.user.instructor_profile
        except ObjectDoesNotExist:
            return render(request, self.template_name, {"error": _("Akademisyen profili bulunamadı.")})

        section = get_object_or_404(CourseSection, pk=section_id)

        # Yetki kontrolü
        if section.offering.instructor != profile:
            return render(request, self.template_name, {"error": _("Yetkiniz yok.")})

        # Öğrencileri ve notlarını getir
        enrollments = Enrollment.objects.filter(
            section=section,
            status=Enrollment.Status.ENROLLED
        ).select_related("student__user", "academic_grade").order_by("student__student_no")

        ctx = {
            "section": section,
            "enrollments": enrollments,
            "grade_choices": [
                ("AA", "AA (4.0)"),
                ("BA", "BA (3.5)"),
                ("BB", "BB (3.0)"),
                ("CB", "CB (2.5)"),
                ("CC", "CC (2.0)"),
                ("DC", "DC (1.5)"),
                ("DD", "DD (1.0)"),
                ("FF", "FF (0.0)"),
            ],
            "breadcrumb_items": items(
                home(),
                {"label": _("Not Girişi"), "url": reverse("instructors:grade_list")},
                {"label": section.offering.course.code, "url": None},
            ),
        }
        return render(request, self.template_name, ctx)

    def post(self, request, section_id):
        from academic.models import CourseSection, Grade
        from enrollments.models import Enrollment
        from django.http import JsonResponse
        from django.shortcuts import get_object_or_404
        from decimal import Decimal
        from audit_logs.services import log_event

        try:
            profile = request.user.instructor_profile
        except ObjectDoesNotExist:
            return JsonResponse({"error": _("Akademisyen profili bulunamadı.")}, status=403)

        section = get_object_or_404(CourseSection, pk=section_id)

        # Yetki kontrolü
        if section.offering.instructor != profile:
            return JsonResponse({"error": _("Yetkiniz yok.")}, status=403)

        # Notları kaydet
        enrollment_id = request.POST.get("enrollment_id")
        letter_grade = request.POST.get("letter_grade", "").strip()
        numeric_grade = request.POST.get("numeric_grade", "").strip()

        if not enrollment_id:
            return JsonResponse({"error": _("Enrollment ID gerekli.")}, status=400)

        enrollment = get_object_or_404(Enrollment, pk=enrollment_id)

        # Yetki ve durum kontrolü
        if enrollment.section != section or enrollment.status != Enrollment.Status.ENROLLED:
            return JsonResponse({"error": _("Geçersiz işlem.")}, status=400)

        # Grade oluştur veya güncelle
        grade, created = Grade.objects.get_or_create(enrollment=enrollment)

        # Numeric grade dönüşümü
        if letter_grade:
            grade_map = {
                "AA": Decimal("4.0"),
                "BA": Decimal("3.5"),
                "BB": Decimal("3.0"),
                "CB": Decimal("2.5"),
                "CC": Decimal("2.0"),
                "DC": Decimal("1.5"),
                "DD": Decimal("1.0"),
                "FF": Decimal("0.0"),
            }
            grade.letter_grade = letter_grade
            grade.numeric_grade = numeric_grade if numeric_grade else grade_map.get(letter_grade)
        else:
            grade.letter_grade = ""
            grade.numeric_grade = None

        grade.save()

        # Audit log
        log_event(
            event_type="grade.entry",
            actor=request.user,
            target_type="academic.Grade",
            target_id=str(grade.pk),
            metadata={
                "student": str(enrollment.student),
                "course": str(enrollment.section.offering.course),
                "letter_grade": letter_grade,
                "numeric_grade": str(grade.numeric_grade) if grade.numeric_grade else "N/A",
            },
            request=request,
        )

        return JsonResponse({"success": True})


# İmport timezone
from django.utils import timezone
