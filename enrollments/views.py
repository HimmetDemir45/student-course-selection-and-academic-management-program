from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from django.db.models import Count, ExpressionWrapper, F, IntegerField, Q
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import ListView

from academic.models import CourseSection, Department, Semester
from core.breadcrumbs import home, items
from core.permissions import StudentRequiredMixin
from core.services.audit import EVENT_ENROLLMENT_CREATED, audit_enrollment_event
from core.services.enrollment_atomic import (
    enroll_student_integrity_message,
    enroll_student_in_section_atomic,
)
from core.services.enrollment_rules import collect_enrollment_preview_messages, is_within_add_drop
from core.services.enrollment_workflow import transition_enrollment_status

from .models import Enrollment


class SectionBrowseView(LoginRequiredMixin, ListView):
    """Aktif section listesi; ogrenci kayit, diger roller onizleme."""

    model = CourseSection
    template_name = "enrollments/section_list.html"
    context_object_name = "sections"
    paginate_by = 25

    def get_queryset(self):
        active_status_q = Q(
            enrollments__status__in=(Enrollment.Status.ENROLLED, Enrollment.Status.PENDING)
        )
        qs = (
            CourseSection.objects.filter(is_active=True, offering__is_active=True)
            .select_related(
                "offering",
                "offering__course",
                "offering__course__department",
                "offering__semester",
                "offering__instructor__user",
            )
            .annotate(active_enrollment_count=Count("enrollments", filter=active_status_q))
            .annotate(effective_quota=Coalesce(F("max_enrollment"), F("offering__quota")))
            .annotate(
                open_seats=ExpressionWrapper(
                    F("effective_quota") - F("active_enrollment_count"),
                    output_field=IntegerField(),
                )
            )
        )
        rq = self.request.GET
        q = (rq.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(offering__course__code__icontains=q)
                | Q(offering__course__name__icontains=q)
            )
        sem = rq.get("semester")
        if sem and str(sem).isdigit():
            qs = qs.filter(offering__semester_id=int(sem))
        dep = rq.get("department")
        if dep and str(dep).isdigit():
            qs = qs.filter(offering__course__department_id=int(dep))
        if rq.get("avail") == "1":
            qs = qs.filter(open_seats__gt=0)
        sort = rq.get("sort") or "code"
        if sort == "code_desc":
            qs = qs.order_by("-offering__course__code", "offering__section")
        elif sort == "cap":
            qs = qs.order_by("open_seats", "offering__course__code")
        elif sort == "cap_desc":
            qs = qs.order_by("-open_seats", "offering__course__code")
        elif sort == "semester":
            qs = qs.order_by(
                "-offering__semester__academic_year",
                "offering__semester__term",
                "offering__course__code",
            )
        else:
            qs = qs.order_by("offering__course__code", "offering__section")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Pano"), "url": reverse("dashboard:index")},
            {"label": _("Ders kaydı (şubeler)"), "url": None},
        )
        ctx["filter_semesters"] = Semester.objects.filter(is_active=True).order_by(
            "-academic_year", "term"
        )
        ctx["filter_departments"] = Department.objects.filter(is_active=True).order_by("code")
        ctx["current_filters"] = {
            "q": self.request.GET.get("q", "").strip(),
            "semester": self.request.GET.get("semester", ""),
            "department": self.request.GET.get("department", ""),
            "avail": self.request.GET.get("avail", ""),
            "sort": self.request.GET.get("sort", "code"),
        }
        for sec in ctx["sections"]:
            cap = getattr(sec, "effective_quota", None) or 0
            used = getattr(sec, "active_enrollment_count", 0) or 0
            pct = min(100, int(round(100 * used / cap))) if cap else 0
            setattr(sec, "capacity_pct", pct)
        user = self.request.user
        if user.is_authenticated and getattr(user, "role", None) == "student":
            try:
                profile = user.student_profile
            except ObjectDoesNotExist:
                profile = None
            if profile:
                # Öğrencinin aktif kayıtları — "zaten kayıtlı" tespiti + özet panel
                active_enrollments = (
                    Enrollment.objects.filter(
                        student=profile,
                        status__in=(Enrollment.Status.ENROLLED, Enrollment.Status.PENDING),
                    )
                    .select_related(
                        "section__offering__course",
                        "section__offering__semester",
                        "section__offering__instructor__user",
                    )
                    .order_by("section__offering__course__code")
                )
                enrolled_section_ids = set(e.section_id for e in active_enrollments)
                ctx["my_enrollments"] = active_enrollments
                ctx["enrolled_section_ids"] = enrolled_section_ids

                for sec in ctx["sections"]:
                    sec.is_enrolled = sec.pk in enrolled_section_ids
                    if not sec.is_enrolled:
                        setattr(
                            sec,
                            "enrollment_preview",
                            collect_enrollment_preview_messages(profile, sec),
                        )
        return ctx


class _StudentEnrollViewBase(StudentRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            profile = request.user.student_profile
        except ObjectDoesNotExist:
            messages.error(request, _("Öğrenci profiliniz bulunamadı."))
            return redirect("enrollments:browse")
        try:
            enr = enroll_student_in_section_atomic(profile, request.POST.get("section_id"))
        except CourseSection.DoesNotExist:
            messages.error(request, _("Şube bulunamadı veya etkin değil."))
        except IntegrityError:
            messages.error(request, enroll_student_integrity_message())
        except ValidationError as exc:
            messages.error(request, _validation_message(exc))
        else:
            audit_enrollment_event(
                EVENT_ENROLLMENT_CREATED,
                actor=request.user,
                enrollment=enr,
                request=request,
            )
            messages.success(request, _("Ders kaydı alındı."))
        return redirect("enrollments:browse")


if settings.FEATURE_FLAGS.get("enrollment_ratelimit", True) and getattr(
    settings, "RATELIMIT_ENABLE", True
):
    from django_ratelimit.decorators import ratelimit

    StudentEnrollView = method_decorator(
        ratelimit(key="user", rate="60/m", method="POST"),
        name="post",
    )(_StudentEnrollViewBase)
else:
    StudentEnrollView = _StudentEnrollViewBase


class StudentDropEnrollmentView(StudentRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            profile = request.user.student_profile
        except ObjectDoesNotExist:
            messages.error(request, _("Öğrenci profiliniz bulunamadı."))
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
            messages.success(request, _("Ders bırakıldı."))
        return redirect("enrollments:browse")


class MyEnrollmentsView(StudentRequiredMixin, View):
    template_name = "enrollments/my_enrollments.html"

    def get(self, request):
        from itertools import groupby as itr_groupby
        from django.shortcuts import render as dj_render
        from django.utils import timezone as tz

        try:
            profile = request.user.student_profile
        except ObjectDoesNotExist:
            return redirect("students:index")

        active_semesters = list(
            Semester.objects.filter(is_active=True).order_by("-academic_year", "term")
        )
        today = tz.localdate()
        current_semester = next(
            (s for s in active_semesters if s.start_date <= today <= s.end_date),
            active_semesters[0] if active_semesters else None,
        )

        all_enr = list(
            Enrollment.objects.filter(
                student=profile,
                status__in=(Enrollment.Status.PENDING, Enrollment.Status.ENROLLED),
            )
            .select_related(
                "section__offering__course",
                "section__offering__semester",
                "section__offering__instructor__user",
                "section__offering__classroom",
            )
            .prefetch_related("section__time_slots")
            .order_by(
                "-section__offering__semester__academic_year",
                "section__offering__course__code",
            )
        )

        sem_blocks = []
        for _sid, group_iter in itr_groupby(all_enr, key=lambda e: e.section.offering.semester_id):
            rows = list(group_iter)
            sem = rows[0].section.offering.semester
            within_window = is_within_add_drop(sem)
            pending_rows = [e for e in rows if e.status == Enrollment.Status.PENDING]
            enrolled_rows = [e for e in rows if e.status == Enrollment.Status.ENROLLED]
            total_credits = sum(e.section.offering.course.credits or 0 for e in rows)
            sem_blocks.append({
                "semester": sem,
                "within_window": within_window,
                "pending_rows": pending_rows,
                "enrolled_rows": enrolled_rows,
                "total_credits": total_credits,
            })

        return dj_render(
            request,
            self.template_name,
            {
                "profile": profile,
                "sem_blocks": sem_blocks,
                "current_semester": current_semester,
                "breadcrumb_items": items(
                    home(),
                    {"label": _("Öğrenci alanı"), "url": reverse("students:index")},
                    {"label": _("Ders seçimlerim"), "url": None},
                ),
            },
        )


def _validation_message(exc: ValidationError) -> str:
    if hasattr(exc, "message_dict"):
        parts = []
        for v in exc.message_dict.values():
            parts.extend(v)
        return "; ".join(parts) if parts else str(exc)
    if exc.messages:
        return "; ".join(exc.messages)
    return str(exc)
