from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.breadcrumbs import home, items
from core.permissions import AdminRequiredMixin, InstructorRequiredMixin

from enrollments.models import Enrollment

from .forms import AnnouncementForm, DepartmentForm, GradeForm
from .models import Announcement, Department, Grade, Semester
from core.services.audit import audit_grade_event
from core.services.enrollment_workflow import transition_enrollment_status


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
            base = qs.filter(is_active=True).filter(role_filter)
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
