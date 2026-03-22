from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView

from core.permissions import StudentRequiredMixin
from core.services.gpa import gpa_from_completed_enrollments

from enrollments.models import Enrollment


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
        return ctx


class StudentIndexView(LoginRequiredMixin, TemplateView):
    template_name = "students/index.html"
