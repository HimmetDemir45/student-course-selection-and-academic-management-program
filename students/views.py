"""
Öğrenci view'ları: dashboard, transkript, müfredat planı, devamsızlık, seçmeli ders havuzu, mezuniyet takibi.
"""
from itertools import groupby

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import ListView, TemplateView, UpdateView

from core.breadcrumbs import home, items
from core.permissions import AdminRequiredMixin, StudentRequiredMixin
from core.services.gpa import gpa_from_completed_enrollments
from core.services.graduation import calculate_graduation_progress

from enrollments.models import Enrollment
from .forms import StudentAssignForm
from .models import StudentProfile


class TranscriptView(StudentRequiredMixin, TemplateView):
    template_name = "students/transcript.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            profile = self.request.user.student_profile
        except ObjectDoesNotExist:
            ctx["enrollments"] = []
            ctx["gpa"] = None
            ctx["gpa_credits"] = 0
            ctx["no_profile"] = True
            ctx["semester_blocks"] = []
            ctx["breadcrumb_items"] = items(
                home(),
                {"label": _("Öğrenci alanı"), "url": reverse("students:index")},
                {"label": _("Transkript"), "url": None},
            )
            return ctx
        qs = (
            Enrollment.objects.filter(student=profile)
            .select_related(
                "section__offering__course",
                "section__offering__semester",
                "academic_grade",
            )
            .order_by("-section__offering__semester__academic_year", "section__offering__course__code")
        )
        ctx["enrollments"] = qs
        gpa, credits = gpa_from_completed_enrollments(qs)
        ctx["gpa"] = gpa
        ctx["gpa_credits"] = credits
        ctx["no_profile"] = False

        all_list = list(qs)
        chron = sorted(all_list, key=lambda e: e.section.offering.semester.start_date)
        ordered = sorted(
            all_list,
            key=lambda e: e.section.offering.semester.start_date,
            reverse=True,
        )
        semester_blocks = []
        for _sem_id, group_iter in groupby(ordered, key=lambda e: e.section.offering.semester_id):
            rows = list(group_iter)
            sem = rows[0].section.offering.semester
            sem_completed = [e for e in rows if e.status == Enrollment.Status.COMPLETED]
            semester_gpa, sem_cred = gpa_from_completed_enrollments(sem_completed)
            cum_completed = [
                e
                for e in chron
                if e.status == Enrollment.Status.COMPLETED
                and e.section.offering.semester.start_date <= sem.start_date
            ]
            cumulative_gpa, _unused_credits = gpa_from_completed_enrollments(cum_completed)
            semester_blocks.append(
                {
                    "semester": sem,
                    "rows": rows,
                    "semester_gpa": semester_gpa,
                    "semester_credits": sem_cred,
                    "cumulative_gpa": cumulative_gpa,
                }
            )
        ctx["semester_blocks"] = semester_blocks

        # Aktif dönem — devam eden kayıtlar
        from academic.models import Semester as SemesterModel
        active_sems = SemesterModel.objects.filter(is_active=True)
        active_enrollments = (
            Enrollment.objects.filter(
                student=profile,
                status__in=(Enrollment.Status.ENROLLED, Enrollment.Status.PENDING),
                section__offering__semester__in=active_sems,
            )
            .select_related(
                "section__offering__course",
                "section__offering__semester",
                "academic_grade",
            )
            .order_by("section__offering__course__code")
        )
        active_list = list(active_enrollments)
        if active_list:
            graded = [e for e in active_list if hasattr(e, "academic_grade") and e.academic_grade and e.academic_grade.letter_grade]
            in_progress_gpa, in_progress_credits = gpa_from_completed_enrollments(graded)
            ctx["active_block"] = {
                "semester": active_list[0].section.offering.semester,
                "rows": active_list,
                "in_progress_gpa": in_progress_gpa,
                "in_progress_credits": in_progress_credits,
                "graded_count": len(graded),
                "total_count": len(active_list),
            }
        else:
            ctx["active_block"] = None

        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Öğrenci alanı"), "url": reverse("students:index")},
            {"label": _("Transkript"), "url": None},
        )
        return ctx


class StudentIndexView(LoginRequiredMixin, View):
    template_name = "students/index.html"

    def get(self, request):
        try:
            profile = request.user.student_profile
        except ObjectDoesNotExist:
            profile = None

        enrollment_count = None
        gpa = None
        gpa_credits = 0

        if profile:
            enrollment_count = Enrollment.objects.filter(
                student=profile,
                status__in=(Enrollment.Status.ENROLLED, Enrollment.Status.PENDING),
            ).count()
            completed = list(
                Enrollment.objects.filter(
                    student=profile, status=Enrollment.Status.COMPLETED
                ).select_related("academic_grade")
            )
            gpa, gpa_credits = gpa_from_completed_enrollments(completed)

        return render(request, self.template_name, {
            "profile": profile,
            "enrollment_count": enrollment_count,
            "gpa": gpa,
            "gpa_credits": gpa_credits,
        })


class GraduationProgressView(StudentRequiredMixin, TemplateView):
    template_name = "students/graduation_progress.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            profile = self.request.user.student_profile
        except ObjectDoesNotExist:
            ctx["progress"] = None
            ctx["no_profile"] = True
            ctx["breadcrumb_items"] = items(
                home(),
                {"label": _("Öğrenci alanı"), "url": reverse("students:index")},
                {"label": _("Mezuniyet takibi"), "url": None},
            )
            return ctx

        progress = calculate_graduation_progress(profile)
        ctx["progress"] = progress
        ctx["profile"] = profile
        ctx["no_profile"] = False
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Öğrenci alanı"), "url": reverse("students:index")},
            {"label": _("Mezuniyet takibi"), "url": None},
        )
        return ctx


class CurriculumPlanView(StudentRequiredMixin, TemplateView):
    template_name = "students/curriculum_plan.html"

    def get_context_data(self, **kwargs):
        from academic.models import CurriculumItem
        from itertools import groupby as itr_groupby
        ctx = super().get_context_data(**kwargs)

        try:
            profile = self.request.user.student_profile
        except ObjectDoesNotExist:
            ctx["year_blocks"] = []
            ctx["no_profile"] = True
            ctx["breadcrumb_items"] = items(
                home(),
                {"label": _("Öğrenci alanı"), "url": reverse("students:index")},
                {"label": _("Müfredat planı"), "url": None},
            )
            return ctx

        completed_codes = set(
            Enrollment.objects.filter(
                student=profile, status=Enrollment.Status.COMPLETED
            ).values_list("section__offering__course__code", flat=True)
        )
        enrolled_codes = set(
            Enrollment.objects.filter(
                student=profile,
                status__in=(Enrollment.Status.ENROLLED, Enrollment.Status.PENDING),
            ).values_list("section__offering__course__code", flat=True)
        )

        curriculum_qs = []
        if profile.program:
            curriculum_qs = list(
                CurriculumItem.objects.filter(program=profile.program)
                .select_related("course")
                .order_by("year_level", "term", "order", "course__code")
            )

        year_blocks = []
        for year, year_iter in itr_groupby(curriculum_qs, key=lambda x: x.year_level):
            term_blocks = []
            year_items = list(year_iter)
            year_completed = sum(1 for i in year_items if i.course.code in completed_codes)
            for term, term_iter in itr_groupby(year_items, key=lambda x: x.term):
                rows = []
                for ci in term_iter:
                    status = "none"
                    if ci.course.code in completed_codes:
                        status = "completed"
                    elif ci.course.code in enrolled_codes:
                        status = "enrolled"
                    rows.append({"item": ci, "status": status})
                term_label = {"fall": _("Güz"), "spring": _("Bahar"), "summer": _("Yaz")}.get(term, term)
                term_blocks.append({
                    "term": term,
                    "term_label": term_label,
                    "rows": rows,
                    "total": len(rows),
                    "completed": sum(1 for r in rows if r["status"] == "completed"),
                })
            year_blocks.append({
                "year": year,
                "term_blocks": term_blocks,
                "total": len(year_items),
                "completed": year_completed,
            })

        ctx["year_blocks"] = year_blocks
        ctx["no_profile"] = False
        ctx["no_program"] = profile.program is None
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Öğrenci alanı"), "url": reverse("students:index")},
            {"label": _("Müfredat planı"), "url": None},
        )
        return ctx


class ElectivePoolStudentView(StudentRequiredMixin, TemplateView):
    template_name = "students/elective_pools.html"

    def get_context_data(self, **kwargs):
        from courses.models import ElectivePool
        ctx = super().get_context_data(**kwargs)
        try:
            profile = self.request.user.student_profile
        except ObjectDoesNotExist:
            ctx["pools"] = []
            ctx["no_profile"] = True
            ctx["breadcrumb_items"] = items(
                home(),
                {"label": _("Öğrenci alanı"), "url": reverse("students:index")},
                {"label": _("Seçmeli dersler"), "url": None},
            )
            return ctx

        completed_codes = set(
            Enrollment.objects.filter(
                student=profile, status=Enrollment.Status.COMPLETED
            ).values_list("section__offering__course__code", flat=True)
        )
        enrolled_codes = set(
            Enrollment.objects.filter(
                student=profile,
                status__in=(Enrollment.Status.ENROLLED, Enrollment.Status.PENDING),
            ).values_list("section__offering__course__code", flat=True)
        )

        pools = []
        if profile.program:
            for pool in (
                ElectivePool.objects.filter(program=profile.program, is_active=True)
                .prefetch_related("courses__department")
                .order_by("name")
            ):
                course_items = []
                completed_in_pool = 0
                for c in pool.courses.filter(is_active=True).order_by("code"):
                    status = "none"
                    if c.code in completed_codes:
                        status = "completed"
                        completed_in_pool += 1
                    elif c.code in enrolled_codes:
                        status = "enrolled"
                    course_items.append({"course": c, "status": status})
                pools.append({
                    "pool": pool,
                    "courses": course_items,
                    "completed_count": completed_in_pool,
                    "done": completed_in_pool >= pool.required_count,
                })

        ctx["pools"] = pools
        ctx["no_profile"] = False
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Öğrenci alanı"), "url": reverse("students:index")},
            {"label": _("Seçmeli dersler"), "url": None},
        )
        return ctx


class StudentAttendanceView(StudentRequiredMixin, TemplateView):
    template_name = "students/attendance.html"

    def get_context_data(self, **kwargs):
        from academic.models import AttendanceEntry, AttendanceRecord
        ctx = super().get_context_data(**kwargs)
        try:
            profile = self.request.user.student_profile
        except ObjectDoesNotExist:
            ctx["enrollment_blocks"] = []
            ctx["no_profile"] = True
            ctx["breadcrumb_items"] = items(
                home(),
                {"label": _("Öğrenci alanı"), "url": reverse("students:index")},
                {"label": _("Devamsızlık"), "url": None},
            )
            return ctx

        enrollments = list(
            Enrollment.objects.filter(
                student=profile,
                status__in=(Enrollment.Status.ENROLLED, Enrollment.Status.COMPLETED),
            )
            .select_related("section__offering__course", "section__offering__semester")
            .order_by("-section__offering__semester__academic_year", "section__offering__course__code")
        )

        enrollment_blocks = []
        for enr in enrollments:
            records = list(AttendanceRecord.objects.filter(section=enr.section).order_by("-date"))
            total = len(records)
            record_ids = [r.pk for r in records]
            entries = list(
                AttendanceEntry.objects.filter(record_id__in=record_ids, student=profile)
            )
            entry_map = {e.record_id: e for e in entries}

            present = sum(1 for e in entries if e.status in ("present", "late"))
            absent = sum(1 for e in entries if e.status == "absent")
            excused = sum(1 for e in entries if e.status == "excused")
            pct = round(present / total * 100) if total > 0 else None

            recent_rows = []
            for rec in records[:8]:
                entry = entry_map.get(rec.pk)
                recent_rows.append({"date": rec.date, "status": entry.status if entry else None})

            enrollment_blocks.append({
                "enrollment": enr,
                "total": total,
                "present": present,
                "absent": absent,
                "excused": excused,
                "pct": pct,
                "recent_rows": recent_rows,
            })

        ctx["enrollment_blocks"] = enrollment_blocks
        ctx["no_profile"] = False
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Öğrenci alanı"), "url": reverse("students:index")},
            {"label": _("Devamsızlık"), "url": None},
        )
        return ctx


class StudentAdminListView(AdminRequiredMixin, ListView):
    model = StudentProfile
    template_name = "students/admin_list.html"
    context_object_name = "students"
    paginate_by = 30

    def get_queryset(self):
        qs = StudentProfile.objects.select_related(
            "user", "department", "program", "advisor__user"
        )
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(student_no__icontains=q)
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
        return qs.order_by("student_no")

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
            {"label": _("Öğrenci yönetimi"), "url": None},
        )
        return ctx


class StudentAdminEditView(AdminRequiredMixin, UpdateView):
    model = StudentProfile
    form_class = StudentAssignForm
    template_name = "students/admin_form.html"
    success_url = reverse_lazy("students:admin_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            _("%(no)s numaralı öğrencinin bilgileri güncellendi.") % {
                "no": self.object.student_no
            },
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Öğrenci yönetimi"), "url": reverse("students:admin_list")},
            {"label": _("Öğrenci düzenle"), "url": None},
        )
        return ctx
