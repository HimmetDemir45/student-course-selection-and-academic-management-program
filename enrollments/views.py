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

from academic.models import CourseSection, CurriculumItem, Department, Semester
from courses.models import ElectivePool
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

    def _student_department(self):
        """Öğrencinin bağlı olduğu bölümü döner; yoksa None."""
        user = self.request.user
        if not (user.is_authenticated and getattr(user, "role", None) == "student"):
            return None
        try:
            return user.student_profile.department
        except ObjectDoesNotExist:
            return None

    def _student_program(self):
        """Öğrencinin programını döner; yoksa None."""
        user = self.request.user
        if not (user.is_authenticated and getattr(user, "role", None) == "student"):
            return None
        try:
            return user.student_profile.program
        except ObjectDoesNotExist:
            return None

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

        # Daha önce F dışı notla geçilen dersleri listeden çıkar.
        user = self.request.user
        if user.is_authenticated and getattr(user, "role", None) == "student":
            try:
                profile = user.student_profile
                passed_course_ids = (
                    Enrollment.objects.filter(
                        student=profile,
                        status=Enrollment.Status.COMPLETED,
                    )
                    .exclude(academic_grade__letter_grade="")
                    .exclude(academic_grade__letter_grade__istartswith="F")
                    .values_list("section__offering__course_id", flat=True)
                )
                if passed_course_ids:
                    qs = qs.exclude(offering__course_id__in=list(passed_course_ids))
            except ObjectDoesNotExist:
                pass

        # Bölüm/program filtresi: açıkça seçilmişse onu kullan;
        # öğrenci rolüyse ve filtre yok → programın müfredat derslerini göster.
        dep_param = rq.get("department", "").strip()
        if dep_param == "all":
            pass  # Öğrenci tüm dersleri görmek istiyor
        elif dep_param and dep_param.isdigit():
            qs = qs.filter(offering__course__department_id=int(dep_param))
        else:
            # Hiç filtre yok — öğrenciyse program müfredatına göre kısıtla
            own_program = self._student_program()
            if own_program is not None:
                curriculum_ids = set(
                    CurriculumItem.objects.filter(program=own_program)
                    .values_list("course_id", flat=True)
                )
                elective_ids = set(
                    ElectivePool.objects.filter(program=own_program, is_active=True)
                    .values_list("courses", flat=True)
                )
                allowed_ids = curriculum_ids | elective_ids
                qs = qs.filter(offering__course_id__in=allowed_ids)
            else:
                own_dept = self._student_department()
                if own_dept is not None:
                    qs = qs.filter(offering__course__department=own_dept)

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
        dep_param = self.request.GET.get("department", "").strip()
        ctx["current_filters"] = {
            "q": self.request.GET.get("q", "").strip(),
            "semester": self.request.GET.get("semester", ""),
            "department": dep_param,
            "avail": self.request.GET.get("avail", ""),
            "sort": self.request.GET.get("sort", "code"),
        }
        # Öğrenci için program/bölüm kısıtlama bilgisi
        own_dept = self._student_department()
        own_program = self._student_program()
        ctx["own_department"] = own_dept
        ctx["own_program"] = own_program
        ctx["showing_all_departments"] = (dep_param == "all")
        # Onay durumu uyarısı
        ctx["student_not_approved"] = False
        user = self.request.user
        if user.is_authenticated and getattr(user, "role", None) == "student":
            try:
                ctx["student_not_approved"] = not user.student_profile.is_approved
            except ObjectDoesNotExist:
                pass
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

                waitlisted_section_ids = set(
                    Enrollment.objects.filter(
                        student=profile,
                        status=Enrollment.Status.WAITLISTED,
                    ).values_list("section_id", flat=True)
                )

                ctx["my_enrollments"] = active_enrollments
                ctx["enrolled_section_ids"] = enrolled_section_ids

                for sec in ctx["sections"]:
                    sec.is_enrolled = sec.pk in enrolled_section_ids
                    sec.is_waitlisted = sec.pk in waitlisted_section_ids
                    if not sec.is_enrolled and not sec.is_waitlisted:
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


class StudentWaitlistView(StudentRequiredMixin, View):
    """Öğrenci bekleme listesine eklenir (kapasite dolduğunda)."""

    def post(self, request, *args, **kwargs):
        try:
            profile = request.user.student_profile
        except ObjectDoesNotExist:
            messages.error(request, _("Öğrenci profiliniz bulunamadı."))
            return redirect("enrollments:browse")

        if not profile.is_approved:
            messages.error(request, _("Hesabınız henüz yönetici tarafından onaylanmamış."))
            return redirect("enrollments:browse")

        from academic.models import CourseSection
        from django.db import IntegrityError as IE

        pk = request.POST.get("section_id")
        try:
            pk = int(pk)
        except (TypeError, ValueError):
            messages.error(request, _("Geçersiz şube seçimi."))
            return redirect("enrollments:browse")

        section = get_object_or_404(
            CourseSection,
            pk=pk,
            is_active=True,
            offering__is_active=True,
            offering__semester__is_active=True,
        )

        existing = Enrollment.objects.filter(student=profile, section=section).first()
        if existing:
            if existing.status in (Enrollment.Status.ENROLLED, Enrollment.Status.PENDING):
                messages.info(request, _("Bu derse zaten kayıtlısın."))
            elif existing.status == Enrollment.Status.WAITLISTED:
                messages.info(request, _("Zaten bekleme listesindelsin."))
            else:
                # DROPPED/WITHDRAWN → WAITLISTED
                Enrollment.objects.filter(pk=existing.pk).update(status=Enrollment.Status.WAITLISTED)
                messages.success(request, _("Bekleme listesine alındın."))
            return redirect("enrollments:browse")

        try:
            enr = Enrollment(student=profile, section=section, status=Enrollment.Status.WAITLISTED)
            # bypass full_clean (kapasite dolu olduğunda çalıştırıyoruz)
            super(Enrollment, enr).save(force_insert=True)
            messages.success(request, _("Bekleme listesine alındın. Yer açıldığında otomatik olarak kayıt isteğine alınacaksın."))
        except IE:
            messages.error(request, _("Bu şube için zaten bir kaydın var."))
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
                status__in=(
                    Enrollment.Status.PENDING,
                    Enrollment.Status.ENROLLED,
                    Enrollment.Status.DROPPED,
                ),
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
            dropped_rows = [e for e in rows if e.status == Enrollment.Status.DROPPED]
            total_credits = sum(e.section.offering.course.credits or 0 for e in rows
                                if e.status in (Enrollment.Status.PENDING, Enrollment.Status.ENROLLED))
            sem_blocks.append({
                "semester": sem,
                "within_window": within_window,
                "pending_rows": pending_rows,
                "enrolled_rows": enrolled_rows,
                "dropped_rows": dropped_rows,
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


class StudentMyCourseSelectionsView(StudentRequiredMixin, View):
    """
    Öğrencinin aktif dönemdeki ders seçimlerini gösterir.
    PENDING (danışman onayı beklemekte), ENROLLED (onaylanmış) ve DROPPED (bırakılmış) dersleri gösterir.
    """
    template_name = "enrollments/my_course_selections.html"

    def get(self, request):
        from django.shortcuts import render as dj_render
        from django.utils import timezone as tz

        try:
            profile = request.user.student_profile
        except ObjectDoesNotExist:
            return redirect("students:index")

        # Find current active semester
        active_semesters = list(
            Semester.objects.filter(is_active=True).order_by("-academic_year", "term")
        )
        today = tz.localdate()
        current_semester = next(
            (s for s in active_semesters if s.start_date <= today <= s.end_date),
            active_semesters[0] if active_semesters else None,
        )

        if not current_semester:
            ctx = {
                "profile": profile,
                "current_semester": None,
                "pending_enrollments": [],
                "enrolled_enrollments": [],
                "dropped_enrollments": [],
                "total_credits": 0,
                "within_window": False,
                "breadcrumb_items": items(
                    home(),
                    {"label": _("Öğrenci alanı"), "url": reverse("students:index")},
                    {"label": _("Ders Seçimlerim"), "url": None},
                ),
            }
            return dj_render(request, self.template_name, ctx)

        # Get all enrollments for current semester
        enrollments = list(
            Enrollment.objects.filter(
                student=profile,
                section__offering__semester=current_semester,
            )
            .select_related(
                "section__offering__course",
                "section__offering__instructor__user",
                "section__offering__classroom",
            )
            .prefetch_related("section__time_slots")
            .order_by("section__offering__course__code")
        )

        # Separate by status
        pending_enrollments = [e for e in enrollments if e.status == Enrollment.Status.PENDING]
        enrolled_enrollments = [e for e in enrollments if e.status == Enrollment.Status.ENROLLED]
        dropped_enrollments = [e for e in enrollments if e.status == Enrollment.Status.DROPPED]

        # Calculate total credits
        total_credits = sum(e.section.offering.course.credits or 0 for e in enrollments if e.status in (Enrollment.Status.PENDING, Enrollment.Status.ENROLLED))

        # Check if within add/drop window
        within_window = is_within_add_drop(current_semester)

        ctx = {
            "profile": profile,
            "current_semester": current_semester,
            "pending_enrollments": pending_enrollments,
            "enrolled_enrollments": enrolled_enrollments,
            "dropped_enrollments": dropped_enrollments,
            "total_credits": total_credits,
            "within_window": within_window,
            "breadcrumb_items": items(
                home(),
                {"label": _("Öğrenci alanı"), "url": reverse("students:index")},
                {"label": _("Ders Seçimlerim"), "url": None},
            ),
        }
        return dj_render(request, self.template_name, ctx)


def _validation_message(exc: ValidationError) -> str:
    if hasattr(exc, "message_dict"):
        parts = []
        for v in exc.message_dict.values():
            parts.extend(v)
        return "; ".join(parts) if parts else str(exc)
    if exc.messages:
        return "; ".join(exc.messages)
    return str(exc)
