from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView

from academic.models import CourseSection
from core.permissions import StudentRequiredMixin
from core.services.audit import EVENT_ENROLLMENT_CREATED, audit_enrollment_event
from core.services.enrollment_workflow import transition_enrollment_status

from .models import Enrollment


class SectionBrowseView(LoginRequiredMixin, ListView):
    """Aktif section listesi; ogrenci kayit, diger roller onizleme."""

    model = CourseSection
    template_name = "enrollments/section_list.html"
    context_object_name = "sections"

    def get_queryset(self):
        return (
            CourseSection.objects.filter(is_active=True, offering__is_active=True)
            .select_related(
                "offering",
                "offering__course",
                "offering__semester",
                "offering__instructor__user",
            )
            .order_by("offering__course__code", "offering__section")
        )


class StudentEnrollView(StudentRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        section = get_object_or_404(
            CourseSection,
            pk=request.POST.get("section_id"),
            is_active=True,
            offering__is_active=True,
        )
        try:
            profile = request.user.student_profile
        except ObjectDoesNotExist:
            messages.error(request, "Ogrenci profiliniz bulunamadi.")
            return redirect("enrollments:browse")
        try:
            enr = Enrollment(
                student=profile,
                section=section,
                status=Enrollment.Status.ENROLLED,
            )
            enr.save()
        except ValidationError as exc:
            messages.error(request, _validation_message(exc))
        else:
            audit_enrollment_event(
                EVENT_ENROLLMENT_CREATED,
                actor=request.user,
                enrollment=enr,
                request=request,
            )
            messages.success(request, "Derse kayit alindiniz.")
        return redirect("enrollments:browse")


class StudentDropEnrollmentView(StudentRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            profile = request.user.student_profile
        except ObjectDoesNotExist:
            messages.error(request, "Ogrenci profiliniz bulunamadi.")
            return redirect("enrollments:browse")
        enr = get_object_or_404(Enrollment, pk=pk, student=profile)
        try:
            transition_enrollment_status(
                enr,
                Enrollment.Status.DROPPED,
                actor=request.user,
                request=request,
            )
        except ValidationError as exc:
            messages.error(request, _validation_message(exc))
        else:
            messages.success(request, "Ders birakildi.")
        return redirect("enrollments:browse")


def _validation_message(exc: ValidationError) -> str:
    if hasattr(exc, "message_dict"):
        parts = []
        for v in exc.message_dict.values():
            parts.extend(v)
        return "; ".join(parts) if parts else str(exc)
    if exc.messages:
        return "; ".join(exc.messages)
    return str(exc)
