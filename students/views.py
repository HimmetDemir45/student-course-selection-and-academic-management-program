from itertools import groupby

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
            ctx["semester_blocks"] = []
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
            cumulative_gpa, _ = gpa_from_completed_enrollments(cum_completed)
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
        return ctx


class StudentIndexView(LoginRequiredMixin, TemplateView):
    template_name = "students/index.html"
