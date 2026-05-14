from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from urllib.parse import urlparse

from audit_logs.services import log_event
from core.breadcrumbs import home, items
from core.permissions import AdminRequiredMixin, InstructorRequiredMixin, role_required

from enrollments.models import Enrollment
from courses.models import Course

from .forms import AnnouncementForm, CurriculumItemForm, DepartmentForm, GradeForm, ProgramForm, SectionTimeSlotForm, SemesterForm
from .models import Announcement, AttendanceEntry, AttendanceRecord, CourseSection, CurriculumItem, Department, Grade, Program, Semester, SectionTimeSlot
from core.services.audit import EVENT_ENROLLMENT_STATUS, audit_enrollment_event, audit_grade_event
from core.services.enrollment_workflow import transition_enrollment_status


def _safe_referer(request, fallback: str) -> str:
    """Return HTTP_REFERER only when it points to the same host; otherwise return fallback."""
    referer = request.META.get("HTTP_REFERER", "")
    if referer:
        try:
            parsed = urlparse(referer)
            if not parsed.netloc or parsed.netloc == request.get_host():
                return referer
        except Exception:
            pass
    return fallback


class ProgramListView(AdminRequiredMixin, ListView):
    model = Program
    template_name = "academic/program_list.html"
    context_object_name = "programs"
    paginate_by = 30

    def get_queryset(self):
        qs = Program.objects.select_related("department")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))
        dept = (self.request.GET.get("dept") or "").strip()
        if dept.isdigit():
            qs = qs.filter(department_id=int(dept))
        return qs.order_by("department__code", "code")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["departments"] = Department.objects.filter(is_active=True).order_by("code")
        ctx["current_filters"] = {
            "q": self.request.GET.get("q", "").strip(),
            "dept": self.request.GET.get("dept", ""),
        }
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Programlar"), "url": None},
        )
        return ctx


class ProgramCreateView(AdminRequiredMixin, CreateView):
    model = Program
    form_class = ProgramForm
    template_name = "academic/program_form.html"
    success_url = reverse_lazy("academic:program_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Programlar"), "url": reverse_lazy("academic:program_list")},
            {"label": _("Yeni program"), "url": None},
        )
        return ctx


class ProgramUpdateView(AdminRequiredMixin, UpdateView):
    model = Program
    form_class = ProgramForm
    template_name = "academic/program_form.html"
    success_url = reverse_lazy("academic:program_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Programlar"), "url": reverse_lazy("academic:program_list")},
            {"label": _("Program düzenle"), "url": None},
        )
        return ctx


class ProgramDeleteView(AdminRequiredMixin, DeleteView):
    model = Program
    template_name = "academic/program_confirm_delete.html"
    success_url = reverse_lazy("academic:program_list")


@require_POST
@role_required("admin")
def program_toggle_active(request, pk):
    obj = get_object_or_404(Program, pk=pk)
    previous = obj.is_active
    obj.is_active = not previous
    obj.save(update_fields=["is_active", "updated_at"])
    messages.success(
        request,
        _("'%(name)s' programı %(state)s hale getirildi.") % {
            "name": obj.name,
            "state": _("aktif") if obj.is_active else _("pasif"),
        },
    )
    return redirect(_safe_referer(request, reverse("academic:program_list")))


class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = "academic/department_list.html"
    context_object_name = "departments"
    paginate_by = 25

    def get_queryset(self):
        qs = Department.objects.all()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))
        sort = self.request.GET.get("sort") or "code"
        if sort == "name":
            return qs.order_by("name", "code")
        return qs.order_by("code")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_filters"] = {
            "q": self.request.GET.get("q", "").strip(),
            "sort": self.request.GET.get("sort", "code"),
        }
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Bölümler"), "url": None},
        )
        return ctx


class DepartmentCreateView(AdminRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = "academic/department_form.html"
    success_url = reverse_lazy("academic:department_list")


class DepartmentUpdateView(AdminRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = "academic/department_form.html"
    success_url = reverse_lazy("academic:department_list")


class DepartmentDeleteView(AdminRequiredMixin, DeleteView):
    model = Department
    template_name = "academic/department_confirm_delete.html"
    success_url = reverse_lazy("academic:department_list")


class AnnouncementListView(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = "academic/announcement_list.html"
    context_object_name = "announcements"
    paginate_by = 25

    def get_queryset(self):
        qs = Announcement.objects.select_related("semester", "department", "published_by")
        user = self.request.user
        if user.role == "admin":
            base = qs
        else:
            role_filter = Q(target_role="all") | Q(target_role=user.role)
            # Bölüm filtresi: department=None ise herkese, set ise sadece o bölüme
            user_dept_id = None
            if user.role == "student":
                try:
                    user_dept_id = user.student_profile.department_id
                except ObjectDoesNotExist:
                    pass
            elif user.role == "instructor":
                try:
                    user_dept_id = user.instructor_profile.department_id
                except ObjectDoesNotExist:
                    pass
            if user_dept_id:
                dept_filter = Q(department__isnull=True) | Q(department_id=user_dept_id)
            else:
                dept_filter = Q(department__isnull=True)
            base = qs.filter(is_active=True).filter(role_filter).filter(dept_filter)
        q = (self.request.GET.get("q") or "").strip()
        if q:
            base = base.filter(Q(title__icontains=q) | Q(body__icontains=q))
        sem = self.request.GET.get("semester")
        if sem and str(sem).isdigit():
            base = base.filter(semester_id=int(sem))
        sort = self.request.GET.get("sort") or "new"
        if sort == "title":
            return base.order_by("title", "-created_at")
        return base.order_by("-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter_semesters"] = Semester.objects.filter(is_active=True).order_by("-academic_year", "term")
        ctx["current_filters"] = {
            "q": self.request.GET.get("q", "").strip(),
            "semester": self.request.GET.get("semester", ""),
            "sort": self.request.GET.get("sort", "new"),
        }
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Duyurular"), "url": None},
        )
        return ctx


class AnnouncementCreateView(AdminRequiredMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = "academic/announcement_form.html"
    success_url = reverse_lazy("academic:announcement_list")

    def form_valid(self, form):
        form.instance.published_by = self.request.user
        return super().form_valid(form)


class AnnouncementUpdateView(AdminRequiredMixin, UpdateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = "academic/announcement_form.html"
    success_url = reverse_lazy("academic:announcement_list")


class AnnouncementDeleteView(AdminRequiredMixin, DeleteView):
    model = Announcement
    template_name = "academic/announcement_confirm_delete.html"
    success_url = reverse_lazy("academic:announcement_list")


def _assert_can_grade(user, enrollment: Enrollment) -> None:
    if user.role == "admin":
        return
    if user.role != "instructor":
        raise PermissionDenied
    try:
        inst = user.instructor_profile
    except ObjectDoesNotExist as exc:
        raise PermissionDenied from exc
    if enrollment.section.offering.instructor_id != inst.pk:
        raise PermissionDenied


class InstructorEnrollmentListView(InstructorRequiredMixin, ListView):
    model = Enrollment
    template_name = "academic/instructor_enrollment_list.html"
    context_object_name = "enrollments"
    paginate_by = 30

    def get_queryset(self):
        user = self.request.user
        qs = Enrollment.objects.select_related(
            "student__user",
            "section__offering__course",
            "section__offering__semester",
            "academic_grade",
        ).filter(
            status__in=(
                Enrollment.Status.ENROLLED,
                Enrollment.Status.PENDING,
                Enrollment.Status.COMPLETED,
            ),
            section__offering__semester__is_active=True,
        ).order_by("section__offering__course__code", "section__offering__section", "student__student_no")
        if user.role == "admin":
            pass
        else:
            try:
                inst = user.instructor_profile
            except ObjectDoesNotExist:
                return Enrollment.objects.none()
            qs = qs.filter(section__offering__instructor=inst)
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(section__offering__course__code__icontains=q)
                | Q(section__offering__course__name__icontains=q)
                | Q(student__student_no__icontains=q)
                | Q(student__user__username__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_filters"] = {"q": self.request.GET.get("q", "").strip()}
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Pano"), "url": reverse("dashboard:index")},
            {"label": _("Öğrenci kayıtları ve notlar"), "url": None},
        )
        seen = set()
        quick = []
        for e in ctx["enrollments"]:
            sid = e.section_id
            if sid in seen:
                continue
            seen.add(sid)
            o = e.section.offering
            quick.append(
                {
                    "anchor": f"sec-{sid}",
                    "label": f"{o.course.code} / {o.section}",
                }
            )
        ctx["section_quick_links"] = quick
        ctx["all_courses"] = Course.objects.order_by("code").values("pk", "code", "name", "credits")
        return ctx


class GradeEntryView(InstructorRequiredMixin, View):
    template_name = "academic/grade_form.html"

    def get(self, request, enrollment_id):
        enrollment = get_object_or_404(
            Enrollment.objects.select_related(
                "section__offering",
                "student__user",
            ),
            pk=enrollment_id,
        )
        _assert_can_grade(request.user, enrollment)
        allowed_statuses = (
            Enrollment.Status.ENROLLED,
            Enrollment.Status.PENDING,
            Enrollment.Status.COMPLETED,
        )
        if enrollment.status not in allowed_statuses:
            messages.error(request, _("Bu kayıt için not girilemez (öğrenci dersi bırakmış veya beklemede)."))
            return redirect("academic:instructor_enrollments")
        grade, _created = Grade.objects.get_or_create(enrollment=enrollment)
        form = GradeForm(instance=grade)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "enrollment": enrollment,
                "grade": grade,
                "breadcrumb_items": items(
                    home(),
                    {"label": _("Pano"), "url": reverse("dashboard:index")},
                    {
                        "label": _("Öğrenci kayıtları ve notlar"),
                        "url": reverse("academic:instructor_enrollments"),
                    },
                    {"label": _("Not girişi"), "url": None},
                ),
            },
        )

    def post(self, request, enrollment_id):
        enrollment = get_object_or_404(
            Enrollment.objects.select_related("section__offering"),
            pk=enrollment_id,
        )
        _assert_can_grade(request.user, enrollment)
        grade, _created = Grade.objects.get_or_create(enrollment=enrollment)
        form = GradeForm(request.POST, instance=grade)
        inline_quick = bool(request.POST.get("inline_quick"))
        if form.is_valid():
            form.save()
            # Not girişi = öğretmen öğrenciyi kabul etmiş; instructor_approved'ı doldur
            if not enrollment.instructor_approved:
                from django.utils import timezone as _tz
                try:
                    inst_profile = request.user.instructor_profile
                except ObjectDoesNotExist:
                    inst_profile = None
                Enrollment.objects.filter(pk=enrollment.pk).update(
                    instructor_approved=True,
                    instructor_approved_by=inst_profile,
                    instructor_approved_at=_tz.now(),
                )
                enrollment.instructor_approved = True
            snapshot = {
                "letter_grade": grade.letter_grade,
                "numeric_grade": str(grade.numeric_grade)
                if grade.numeric_grade is not None
                else "",
            }
            audit_grade_event(
                actor=request.user,
                enrollment=enrollment,
                grade_snapshot=snapshot,
                request=request,
            )
            if form.cleaned_data.get("letter_grade"):
                try:
                    transition_enrollment_status(
                        enrollment,
                        Enrollment.Status.COMPLETED,
                        actor=request.user,
                        request=request,
                    )
                except ValidationError as exc:
                    messages.error(request, "; ".join(exc.messages))
                    return render(
                        request,
                        self.template_name,
                        {
                            "form": form,
                            "enrollment": enrollment,
                            "grade": grade,
                            "breadcrumb_items": items(
                                home(),
                                {"label": _("Pano"), "url": reverse("dashboard:index")},
                                {
                                    "label": _("Öğrenci kayıtları ve notlar"),
                                    "url": reverse("academic:instructor_enrollments"),
                                },
                                {"label": _("Not girişi"), "url": None},
                            ),
                        },
                    )
            messages.success(request, _("Not kaydedildi."))
            return redirect("academic:instructor_enrollments")
        if inline_quick:
            parts = []
            if form.non_field_errors():
                parts.extend(form.non_field_errors())
            for field, errs in form.errors.items():
                parts.extend(f"{field}: {e}" for e in errs)
            messages.error(request, "; ".join(parts) if parts else _("Geçersiz not bilgisi."))
            return redirect("academic:instructor_enrollments")
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "enrollment": enrollment,
                "grade": grade,
                "breadcrumb_items": items(
                    home(),
                    {"label": _("Pano"), "url": reverse("dashboard:index")},
                    {
                        "label": _("Öğrenci kayıtları ve notlar"),
                        "url": reverse("academic:instructor_enrollments"),
                    },
                    {"label": _("Not girişi"), "url": None},
                ),
            },
        )


class SemesterListView(AdminRequiredMixin, ListView):
    model = Semester
    template_name = "academic/semester_list.html"
    context_object_name = "semesters"
    paginate_by = 20

    def get_queryset(self):
        qs = Semester.objects.all()
        term = self.request.GET.get("term", "").strip()
        if term in ("fall", "spring", "summer"):
            qs = qs.filter(term=term)
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(academic_year__icontains=q))
        return qs.order_by("-academic_year", "term")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_filters"] = {
            "q": self.request.GET.get("q", "").strip(),
            "term": self.request.GET.get("term", ""),
        }
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Dönemler"), "url": None},
        )
        return ctx


class SemesterCreateView(AdminRequiredMixin, CreateView):
    model = Semester
    form_class = SemesterForm
    template_name = "academic/semester_form.html"
    success_url = reverse_lazy("academic:semester_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Dönemler"), "url": reverse_lazy("academic:semester_list")},
            {"label": _("Yeni dönem"), "url": None},
        )
        return ctx


class SemesterUpdateView(AdminRequiredMixin, UpdateView):
    model = Semester
    form_class = SemesterForm
    template_name = "academic/semester_form.html"
    success_url = reverse_lazy("academic:semester_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Dönemler"), "url": reverse_lazy("academic:semester_list")},
            {"label": _("Dönem düzenle"), "url": None},
        )
        return ctx




class CurriculumListView(AdminRequiredMixin, ListView):
    model = CurriculumItem
    template_name = "academic/curriculum_list.html"
    context_object_name = "items"
    paginate_by = 50

    def get_queryset(self):
        from academic.models import Program
        qs = CurriculumItem.objects.select_related("program", "course")
        prog = self.request.GET.get("program")
        if prog and str(prog).isdigit():
            qs = qs.filter(program_id=int(prog))
        return qs.order_by("program__code", "year_level", "term", "order", "course__code")

    def get_context_data(self, **kwargs):
        from academic.models import Program
        ctx = super().get_context_data(**kwargs)
        ctx["filter_programs"] = Program.objects.filter(is_active=True).order_by("code")
        ctx["current_filters"] = {"program": self.request.GET.get("program", "")}
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Müfredat planı"), "url": None},
        )
        return ctx


class CurriculumItemCreateView(AdminRequiredMixin, CreateView):
    model = CurriculumItem
    form_class = CurriculumItemForm
    template_name = "academic/curriculum_form.html"
    success_url = reverse_lazy("academic:curriculum_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Müfredat planı"), "url": reverse_lazy("academic:curriculum_list")},
            {"label": _("Yeni ders"), "url": None},
        )
        return ctx


class CurriculumItemUpdateView(AdminRequiredMixin, UpdateView):
    model = CurriculumItem
    form_class = CurriculumItemForm
    template_name = "academic/curriculum_form.html"
    success_url = reverse_lazy("academic:curriculum_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Müfredat planı"), "url": reverse_lazy("academic:curriculum_list")},
            {"label": _("Ders düzenle"), "url": None},
        )
        return ctx


class CurriculumItemDeleteView(AdminRequiredMixin, DeleteView):
    model = CurriculumItem
    template_name = "academic/curriculum_confirm_delete.html"
    success_url = reverse_lazy("academic:curriculum_list")


def _get_instructor_or_403(user):
    if user.role == "admin":
        return None  # admin sees all
    try:
        return user.instructor_profile
    except ObjectDoesNotExist:
        raise PermissionDenied


def _assert_is_advisor(user, student_profile):
    if user.role == "admin":
        return
    try:
        inst = user.instructor_profile
    except ObjectDoesNotExist as exc:
        raise PermissionDenied from exc
    if student_profile.advisor_id != inst.pk:
        raise PermissionDenied


class DanismanAdviseeListView(InstructorRequiredMixin, ListView):
    """Danışmanın danışöğrencileri ve bekleyen ders kayıtları özeti."""
    model = None  # StudentProfile üzerinden manuel queryset
    template_name = "academic/danishman_advisee_list.html"
    context_object_name = "advisees"
    paginate_by = 30

    def get_queryset(self):
        from students.models import StudentProfile
        inst = _get_instructor_or_403(self.request.user)
        qs = (
            StudentProfile.objects.select_related("user", "department", "program")
            .annotate(
                pending_count=Count(
                    "enrollments",
                    filter=Q(enrollments__status=Enrollment.Status.PENDING),
                )
            )
            .order_by("student_no")
        )
        if inst is not None:
            qs = qs.filter(advisor=inst)
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(student_no__icontains=q)
                | Q(user__first_name__icontains=q)
                | Q(user__last_name__icontains=q)
            )
        only = self.request.GET.get("only")
        if only == "pending":
            qs = qs.filter(pending_count__gt=0)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_filters"] = {
            "q": self.request.GET.get("q", "").strip(),
            "only": self.request.GET.get("only", ""),
        }
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Pano"), "url": reverse("dashboard:index")},
            {"label": _("Danışöğrencilerim"), "url": None},
        )
        return ctx


class DanismanAdviseeDetailView(InstructorRequiredMixin, View):
    """Bir danışöğrencinin bekleyen ders kayıtları, tümünü onayla."""
    template_name = "academic/danishman_advisee_detail.html"

    def get(self, request, student_pk):
        from students.models import StudentProfile
        student = get_object_or_404(
            StudentProfile.objects.select_related("user", "department", "program", "advisor__user"),
            pk=student_pk,
        )
        _assert_is_advisor(request.user, student)

        pending = (
            Enrollment.objects.filter(student=student, status=Enrollment.Status.PENDING)
            .select_related(
                "section__offering__course",
                "section__offering__semester",
                "section__offering__instructor__user",
                "section__offering__classroom",
            )
            .order_by("section__offering__course__code")
        )
        enrolled = (
            Enrollment.objects.filter(student=student, status=Enrollment.Status.ENROLLED)
            .select_related(
                "section__offering__course",
                "section__offering__semester",
            )
            .order_by("section__offering__course__code")
        )
        total_pending_credits = sum(e.section.offering.course.credits or 0 for e in pending)
        total_enrolled_credits = sum(e.section.offering.course.credits or 0 for e in enrolled)
        return render(
            request,
            self.template_name,
            {
                "student": student,
                "pending": pending,
                "enrolled": enrolled,
                "total_pending_credits": total_pending_credits,
                "total_enrolled_credits": total_enrolled_credits,
                "breadcrumb_items": items(
                    home(),
                    {"label": _("Pano"), "url": reverse("dashboard:index")},
                    {"label": _("Danışöğrencilerim"), "url": reverse("academic:danishman_advisees")},
                    {"label": student.user.get_full_name() or student.student_no, "url": None},
                ),
            },
        )


@require_POST
@role_required("instructor", "admin")
def danishman_approve_all(request, student_pk):
    from students.models import StudentProfile
    from django.utils import timezone as tz

    student = get_object_or_404(StudentProfile.objects.select_related("user"), pk=student_pk)
    _assert_is_advisor(request.user, student)

    pending = list(
        Enrollment.objects.filter(student=student, status=Enrollment.Status.PENDING)
        .select_related("section__offering__semester")
    )
    approved = 0
    errors = []
    for enr in pending:
        try:
            transition_enrollment_status(
                enr,
                Enrollment.Status.ENROLLED,
                actor=request.user,
                request=request,
            )
            approved += 1
        except ValidationError as exc:
            errors.append(f"{enr.section.offering.course.code}: {'; '.join(exc.messages)}")

    if approved:
        messages.success(
            request,
            _("%(name)s için %(n)d ders kaydı onaylandı.") % {
                "name": student.user.get_full_name() or student.student_no,
                "n": approved,
            },
        )
    for err in errors:
        messages.warning(request, err)

    return redirect(reverse("academic:danishman_advisee_detail", kwargs={"student_pk": student_pk}))


@require_POST
@role_required("admin")
def semester_toggle_active(request, pk):
    obj = get_object_or_404(Semester, pk=pk)
    previous = obj.is_active
    obj.is_active = not previous
    obj.save(update_fields=["is_active", "updated_at"])
    log_event(
        event_type="semester.toggle_active",
        actor=request.user,
        target_type="academic.Semester",
        target_id=obj.pk,
        metadata={"from": previous, "to": obj.is_active, "name": obj.name},
        request=request,
    )
    messages.success(
        request,
        _("'%(name)s' dönemi %(state)s hale getirildi.") % {
            "name": obj.name,
            "state": _("aktif") if obj.is_active else _("pasif"),
        },
    )
    return redirect(_safe_referer(request, reverse("academic:semester_list")))


@require_POST
@role_required("admin")
def department_toggle_active(request, pk):
    obj = get_object_or_404(Department, pk=pk)
    previous = obj.is_active
    obj.is_active = not previous
    obj.save(update_fields=["is_active", "updated_at"])
    log_event(
        event_type="department.toggle_active",
        actor=request.user,
        target_type="academic.Department",
        target_id=obj.pk,
        metadata={"from": previous, "to": obj.is_active, "code": obj.code},
        request=request,
    )
    messages.success(
        request,
        _("'%(name)s' bölümü %(state)s hale getirildi.") % {
            "name": obj.name,
            "state": _("aktif") if obj.is_active else _("pasif"),
        },
    )
    return redirect(_safe_referer(request, reverse("academic:department_list")))


@require_POST
@role_required("admin")
def announcement_toggle_active(request, pk):
    obj = get_object_or_404(Announcement, pk=pk)
    previous = obj.is_active
    obj.is_active = not previous
    obj.save(update_fields=["is_active", "updated_at"])
    log_event(
        event_type="announcement.toggle_active",
        actor=request.user,
        target_type="academic.Announcement",
        target_id=obj.pk,
        metadata={"from": previous, "to": obj.is_active, "title": obj.title},
        request=request,
    )
    messages.success(
        request,
        _("'%(title)s' duyurusu %(state)s hale getirildi.") % {
            "title": obj.title,
            "state": _("aktif") if obj.is_active else _("pasif"),
        },
    )
    return redirect(_safe_referer(request, reverse("academic:announcement_list")))


# ── Devamsızlık / Attendance ──────────────────────────────────────────────────

class AttendanceSectionListView(InstructorRequiredMixin, ListView):
    """Akademisyenin derslerinin devamsızlık şubesi listesi."""
    template_name = "academic/attendance_section_list.html"
    context_object_name = "sections"

    def get_queryset(self):
        from academic.models import CourseSection
        inst = _get_instructor_or_403(self.request.user)
        qs = (
            CourseSection.objects
            .select_related("offering__course", "offering__semester", "offering__instructor__user")
            .filter(is_active=True, offering__semester__is_active=True)
            .annotate(record_count=Count("attendance_records"))
        )
        if inst is not None:
            qs = qs.filter(offering__instructor=inst)
        return qs.order_by("-offering__semester__academic_year", "offering__course__code")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Devamsızlık"), "url": None},
        )
        return ctx


class AttendanceTakeView(InstructorRequiredMixin, View):
    """Belirli bir şube için yoklama al / düzenle."""
    template_name = "academic/attendance_take.html"

    def _get_section(self, section_pk, user):
        from academic.models import CourseSection
        inst = _get_instructor_or_403(user)
        section = get_object_or_404(
            CourseSection.objects.select_related(
                "offering__course", "offering__semester", "offering__instructor"
            ),
            pk=section_pk,
        )
        if inst is not None and section.offering.instructor_id != inst.pk:
            raise PermissionDenied
        return section

    def _build_context(self, request, section, sel_date):
        import datetime
        try:
            record = AttendanceRecord.objects.prefetch_related("entries__student__user").get(
                section=section, date=sel_date
            )
            entry_map = {e.student_id: e for e in record.entries.all()}
        except AttendanceRecord.DoesNotExist:
            record = None
            entry_map = {}

        enrolled = list(
            Enrollment.objects.filter(
                section=section,
                status__in=(
                    Enrollment.Status.ENROLLED,
                    Enrollment.Status.PENDING,
                    Enrollment.Status.COMPLETED,
                ),
            )
            .select_related("student__user")
            .order_by("student__student_no")
        )
        student_rows = []
        for enr in enrolled:
            existing = entry_map.get(enr.student_id)
            student_rows.append({
                "student": enr.student,
                "status": existing.status if existing else AttendanceEntry.Status.PRESENT,
                "note": existing.note if existing else "",
            })

        past_records = (
            AttendanceRecord.objects
            .filter(section=section)
            .annotate(
                present_count=Count("entries", filter=Q(entries__status__in=("present", "late"))),
                total_count=Count("entries"),
            )
            .order_by("-date")[:10]
        )

        # build date range for the date picker: semester start → today
        today = datetime.date.today()
        sem_start = section.offering.semester.start_date
        sem_end = min(section.offering.semester.end_date, today)

        return {
            "section": section,
            "sel_date": sel_date,
            "student_rows": student_rows,
            "status_choices": AttendanceEntry.Status.choices,
            "past_records": past_records,
            "record": record,
            "today": today,
            "sem_start": sem_start,
            "sem_end": sem_end,
            "breadcrumb_items": items(
                home(),
                {"label": _("Devamsızlık"), "url": reverse("academic:attendance_sections")},
                {"label": section.offering.course.code, "url": None},
            ),
        }

    def get(self, request, section_pk):
        import datetime
        section = self._get_section(section_pk, request.user)
        from django.utils import timezone as tz
        date_str = request.GET.get("date") or str(tz.localdate())
        try:
            sel_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            sel_date = tz.localdate()
        return render(request, self.template_name, self._build_context(request, section, sel_date))

    def post(self, request, section_pk):
        import datetime
        from django.utils import timezone as tz

        section = self._get_section(section_pk, request.user)
        date_str = request.POST.get("date") or str(tz.localdate())
        try:
            sel_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            sel_date = tz.localdate()

        inst = _get_instructor_or_403(request.user)
        record, _ = AttendanceRecord.objects.get_or_create(
            section=section,
            date=sel_date,
            defaults={"taken_by": inst},
        )

        enrolled = list(
            Enrollment.objects.filter(
                section=section,
                status__in=(Enrollment.Status.ENROLLED, Enrollment.Status.COMPLETED),
            ).select_related("student")
        )
        valid_statuses = {s for s, _ in AttendanceEntry.Status.choices}
        for enr in enrolled:
            status_val = request.POST.get(f"status_{enr.student_id}", AttendanceEntry.Status.PRESENT)
            if status_val not in valid_statuses:
                status_val = AttendanceEntry.Status.PRESENT
            note_val = request.POST.get(f"note_{enr.student_id}", "").strip()
            AttendanceEntry.objects.update_or_create(
                record=record,
                student=enr.student,
                defaults={"status": status_val, "note": note_val},
            )

        messages.success(
            request,
            _("%(date)s tarihli yoklama kaydedildi.") % {"date": sel_date},
        )
        return redirect(
            reverse("academic:attendance_take", kwargs={"section_pk": section_pk})
            + f"?date={sel_date}"
        )


# ---------------------------------------------------------------------------
# SectionTimeSlot CRUD
# ---------------------------------------------------------------------------

# Weekday display names with proper Turkish characters
_WEEKDAY_NAMES = {
    0: "Pazartesi",
    1: "Salı",
    2: "Çarşamba",
    3: "Perşembe",
    4: "Cuma",
    5: "Cumartesi",
    6: "Pazar",
}

_GRID_START_MIN = 8 * 60   # 08:00
_GRID_END_MIN   = 21 * 60  # 21:00  → 780 px total (1 px / min)


class SectionTimeSlotManageView(AdminRequiredMixin, View):
    """Bir ders teklifine (offering) ait zaman dilimlerini yönet."""

    template_name = "academic/timeslot_manage.html"

    def _get_offering_and_section(self, offering_pk):
        from courses.models import CourseOffering
        offering = get_object_or_404(
            CourseOffering.objects.select_related("course", "semester", "instructor__user"),
            pk=offering_pk,
        )
        section, _ = CourseSection.objects.get_or_create(offering=offering)
        return offering, section

    def _build_context(self, offering, section, form=None):
        raw_slots = list(
            section.time_slots.order_by("weekday", "start_time")
        )
        slots_enriched = []
        for s in raw_slots:
            start_min = s.start_time.hour * 60 + s.start_time.minute
            end_min   = s.end_time.hour   * 60 + s.end_time.minute
            slots_enriched.append({
                "slot": s,
                "weekday_name": _WEEKDAY_NAMES.get(s.weekday, s.get_weekday_display()),
                "duration_min": end_min - start_min,
            })
        return {
            "offering": offering,
            "section": section,
            "slots_enriched": slots_enriched,
            "form": form or SectionTimeSlotForm(),
            "breadcrumb_items": items(
                home(),
                {"label": _("Ders teklifleri"), "url": reverse("courses:offering_list")},
                {"label": _("Zaman dilimleri"), "url": None},
            ),
        }

    def get(self, request, offering_pk):
        offering, section = self._get_offering_and_section(offering_pk)
        return render(request, self.template_name, self._build_context(offering, section))

    def post(self, request, offering_pk):
        offering, section = self._get_offering_and_section(offering_pk)
        form = SectionTimeSlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.section = section
            slot.save()
            log_event(
                event_type="timeslot.add",
                actor=request.user,
                target_type="academic.SectionTimeSlot",
                target_id=slot.pk,
                metadata={
                    "offering": str(offering),
                    "weekday": slot.weekday,
                    "start": str(slot.start_time),
                    "end": str(slot.end_time),
                },
                request=request,
            )
            messages.success(
                request,
                _("%(day)s %(start)s–%(end)s zaman dilimi eklendi.") % {
                    "day": _WEEKDAY_NAMES.get(slot.weekday, ""),
                    "start": slot.start_time.strftime("%H:%M"),
                    "end": slot.end_time.strftime("%H:%M"),
                },
            )
            return redirect("academic:timeslot_manage", offering_pk=offering_pk)
        return render(request, self.template_name, self._build_context(offering, section, form))


@require_POST
@role_required("admin")
def timeslot_delete(request, slot_pk):
    slot = get_object_or_404(SectionTimeSlot, pk=slot_pk)
    offering_pk = slot.section.offering_id
    day_label = _WEEKDAY_NAMES.get(slot.weekday, "")
    time_label = f"{slot.start_time.strftime('%H:%M')}–{slot.end_time.strftime('%H:%M')}"
    slot.delete()
    messages.success(request, _("%(day)s %(time)s zaman dilimi kaldırıldı.") % {"day": day_label, "time": time_label})
    return redirect("academic:timeslot_manage", offering_pk=offering_pk)


# ---------------------------------------------------------------------------
# Haftalık Ders Programı
# ---------------------------------------------------------------------------

def _assign_columns(items: list) -> list:
    """
    Aynı gün sütunundaki çakışan kartlara alt-sütun (col_index, col_count) atar.
    items: [{"top_px": int, "height_px": int, ...}, ...]
    Her item'a col_index ve col_count eklenir; orijinal liste döner.
    """
    if not items:
        return items
    sorted_items = sorted(items, key=lambda x: x["top_px"])
    # sub_col_ends[i] = i. alt-sütunun son doldurulan piksel değeri
    sub_col_ends: list[int] = []
    col_indices: list[int] = []

    for it in sorted_items:
        top = it["top_px"]
        bottom = top + it["height_px"]
        placed = False
        for i, end in enumerate(sub_col_ends):
            if top >= end:
                col_indices.append(i)
                sub_col_ends[i] = bottom
                placed = True
                break
        if not placed:
            col_indices.append(len(sub_col_ends))
            sub_col_ends.append(bottom)

    # Overlap gruplarını bul — aynı anda çakışan kartların max alt-sütun sayısı
    for idx, it in enumerate(sorted_items):
        top = it["top_px"]
        bottom = top + it["height_px"]
        max_col = 1
        for jdx, jt in enumerate(sorted_items):
            if idx == jdx:
                continue
            jtop = jt["top_px"]
            jbottom = jtop + jt["height_px"]
            if top < jbottom and jtop < bottom:
                max_col = max(max_col, col_indices[jdx] + 1)
        it["col_index"] = col_indices[idx]
        it["col_count"] = max(max_col, col_indices[idx] + 1)

    return sorted_items


class WeeklyScheduleView(LoginRequiredMixin, View):
    """Kullanıcı rolüne göre haftalık ders programını grid olarak gösterir."""

    template_name = "academic/weekly_schedule.html"

    def get(self, request):
        user = request.user
        sem_id = (request.GET.get("semester") or "").strip()

        base_qs = (
            SectionTimeSlot.objects
            .select_related(
                "section__offering__course",
                "section__offering__instructor__user",
                "section__offering__classroom",
                "section__offering__semester",
            )
            .order_by("weekday", "start_time")
        )

        if user.role == "student":
            try:
                profile = user.student_profile
            except ObjectDoesNotExist:
                profile = None
            if profile:
                enr_qs = Enrollment.objects.filter(
                    student=profile,
                    status__in=[
                        Enrollment.Status.ENROLLED,
                        Enrollment.Status.PENDING,
                    ],
                )
                # Dönem filtresi: URL'de seçili dönem varsa onu kullan,
                # yoksa aktif dönemlere göre filtrele.
                if sem_id.isdigit():
                    enr_qs = enr_qs.filter(section__offering__semester_id=int(sem_id))
                else:
                    active_sem_ids = list(
                        Semester.objects.filter(is_active=True).values_list("pk", flat=True)
                    )
                    if active_sem_ids:
                        enr_qs = enr_qs.filter(section__offering__semester_id__in=active_sem_ids)
                enrolled_ids = enr_qs.values_list("section_id", flat=True)
                slots_qs = base_qs.filter(section_id__in=enrolled_ids)
            else:
                slots_qs = SectionTimeSlot.objects.none()

        elif user.role == "instructor":
            try:
                profile = user.instructor_profile
            except ObjectDoesNotExist:
                profile = None
            if profile:
                slots_qs = base_qs.filter(section__offering__instructor=profile)
                if sem_id.isdigit():
                    slots_qs = slots_qs.filter(section__offering__semester_id=int(sem_id))
                else:
                    active_sem_ids = list(
                        Semester.objects.filter(is_active=True).values_list("pk", flat=True)
                    )
                    if active_sem_ids:
                        slots_qs = slots_qs.filter(section__offering__semester_id__in=active_sem_ids)
            else:
                slots_qs = SectionTimeSlot.objects.none()

        else:  # admin
            slots_qs = base_qs
            if sem_id.isdigit():
                slots_qs = slots_qs.filter(section__offering__semester_id=int(sem_id))
            else:
                active_sem_ids = list(
                    Semester.objects.filter(is_active=True).values_list("pk", flat=True)
                )
                if active_sem_ids:
                    slots_qs = slots_qs.filter(section__offering__semester_id__in=active_sem_ids)

        # Build schedule grid: {weekday: [{"slot":..., "top_px":..., "height_px":...}, ...]}
        schedule = {d: [] for d in range(7)}
        for slot in slots_qs:
            start_min = slot.start_time.hour * 60 + slot.start_time.minute
            end_min   = slot.end_time.hour   * 60 + slot.end_time.minute
            top_px    = max(0, start_min - _GRID_START_MIN)
            height_px = max(20, end_min - start_min)
            schedule[slot.weekday].append({
                "slot": slot,
                "top_px": top_px,
                "height_px": height_px,
            })

        # Determine which days to show (always Mon–Fri minimum; extend if Sat/Sun have data)
        max_day_with_data = max(
            (d for d in range(7) if schedule[d]),
            default=4,
        )
        days_to_show = list(range(max(5, max_day_with_data + 1)))

        # Time ruler: 08:00 → 21:00
        grid_height_px = _GRID_END_MIN - _GRID_START_MIN
        time_labels = []
        h = _GRID_START_MIN // 60
        while h * 60 <= _GRID_END_MIN:
            time_labels.append({
                "label": f"{h:02d}:00",
                "top_px": h * 60 - _GRID_START_MIN,
            })
            h += 1

        # Convert to ordered list of day-columns for easy template iteration
        # _assign_columns adds col_index / col_count for overlap-aware rendering
        schedule_cols = [
            {
                "day": d,
                "name": _WEEKDAY_NAMES.get(d, str(d)),
                "items": _assign_columns(schedule[d]),
            }
            for d in days_to_show
        ]

        # Dönem listesi: öğrenci için kayıtlı olduğu dönemler, diğerleri için aktif dönemler
        if user.role == "student":
            try:
                _profile = user.student_profile
                sem_list = Semester.objects.filter(
                    offerings__section_detail__enrollments__student=_profile,
                    offerings__section_detail__enrollments__status__in=[
                        Enrollment.Status.ENROLLED,
                        Enrollment.Status.PENDING,
                    ],
                ).distinct().order_by("-academic_year", "term")
            except ObjectDoesNotExist:
                sem_list = Semester.objects.none()
        else:
            sem_list = Semester.objects.filter(is_active=True).order_by("-academic_year", "term")

        ctx = {
            "schedule_cols": schedule_cols,
            "time_labels": time_labels,
            "grid_height_px": grid_height_px,
            "col_count": len(days_to_show),
            "semesters": sem_list,
            "selected_semester": sem_id,
            "breadcrumb_items": items(
                home(),
                {"label": _("Haftalık program"), "url": None},
            ),
            "nav_namespace": "academic",
            "nav_url_name": "weekly_schedule",
        }
        return render(request, self.template_name, ctx)


class InstructorReassignCourseView(InstructorRequiredMixin, View):
    """
    Eğitim görevlisi bir PENDING enrollment için alternatif ders önerir.
    POST: enrollment_id, suggested_course_id, note
    """

    def post(self, request, enrollment_id):
        enrollment = get_object_or_404(Enrollment, pk=enrollment_id)

        # Yetki: sadece ilgili dersin eğitim görevlisi veya admin
        if request.user.role != "admin":
            try:
                inst = request.user.instructor_profile
            except ObjectDoesNotExist:
                raise PermissionDenied
            if enrollment.section.offering.instructor != inst:
                raise PermissionDenied

        suggested_id = request.POST.get("suggested_course_id")
        note = request.POST.get("note", "").strip()

        if suggested_id:
            suggested = Course.objects.filter(pk=suggested_id).first()
            if suggested:
                enrollment.reassignment_suggested_course = suggested
                enrollment.reassignment_note = note
                # bypass full_clean (add/drop window vs.)
                super(Enrollment, enrollment).save(update_fields=["reassignment_suggested_course", "reassignment_note"])
                messages.success(
                    request,
                    _("%(student)s için alternatif ders önerisi kaydedildi: %(course)s") % {
                        "student": enrollment.student.user.get_full_name(),
                        "course": suggested.code,
                    },
                )
                log_event(
                    event_type="enrollment.reassignment_suggested",
                    actor=request.user,
                    target_type="enrollments.Enrollment",
                    target_id=str(enrollment.pk),
                    metadata={
                        "suggested_course": suggested.code,
                        "note": note,
                    },
                    request=request,
                )
            else:
                messages.error(request, _("Geçersiz ders seçimi."))
        else:
            messages.error(request, _("Lütfen bir ders seçin."))

        return redirect("academic:instructor_enrollments")
