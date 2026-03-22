from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.permissions import AdminRequiredMixin, InstructorRequiredMixin

from enrollments.models import Enrollment

from .forms import AnnouncementForm, DepartmentForm, GradeForm
from .models import Announcement, Department, Grade
from core.services.audit import audit_grade_event
from core.services.enrollment_workflow import transition_enrollment_status


class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = "academic/department_list.html"
    context_object_name = "departments"


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

    def get_queryset(self):
        qs = Announcement.objects.select_related("semester", "department", "published_by")
        user = self.request.user
        if user.role == "admin":
            return qs

        role_filter = Q(target_role="all") | Q(target_role=user.role)
        return qs.filter(is_active=True).filter(role_filter)


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

    def get_queryset(self):
        user = self.request.user
        qs = Enrollment.objects.select_related(
            "student__user",
            "section__offering__course",
            "section__offering__semester",
        ).order_by("section__offering__course__code", "student__student_no")
        if user.role == "admin":
            return qs
        try:
            inst = user.instructor_profile
        except ObjectDoesNotExist:
            return Enrollment.objects.none()
        return qs.filter(section__offering__instructor=inst)


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
        grade, _ = Grade.objects.get_or_create(enrollment=enrollment)
        form = GradeForm(instance=grade)
        return render(
            request,
            self.template_name,
            {"form": form, "enrollment": enrollment, "grade": grade},
        )

    def post(self, request, enrollment_id):
        enrollment = get_object_or_404(
            Enrollment.objects.select_related("section__offering"),
            pk=enrollment_id,
        )
        _assert_can_grade(request.user, enrollment)
        grade, _ = Grade.objects.get_or_create(enrollment=enrollment)
        form = GradeForm(request.POST, instance=grade)
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
                        {"form": form, "enrollment": enrollment, "grade": grade},
                    )
            messages.success(request, "Not kaydedildi.")
            return redirect("academic:instructor_enrollments")
        return render(
            request,
            self.template_name,
            {"form": form, "enrollment": enrollment, "grade": grade},
        )
