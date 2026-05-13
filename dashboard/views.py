from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import ListView, TemplateView

from accounts.models import AdminRequest, User
from core.breadcrumbs import home, items
from instructors.models import InstructorProfile
from students.models import StudentProfile
from academic.models import Announcement, Semester
from audit_logs.models import AuditLog
from audit_logs.services import log_event
from courses.models import CourseOffering
from core.permissions import FounderAdminRequiredMixin
from core.services.enrollment_rules import is_within_add_drop
from enrollments.models import Enrollment


class DashboardIndexView(LoginRequiredMixin, TemplateView):
    """
    Tüm roller için özet; yönetim linkleri yalnızca admin şablonda gösterilir.
    Rollback: AdminRequiredMixin'e dönün ve şablonu eski haline alın.
    """

    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        role = getattr(u, "role", None)
        ctx["role"] = role
        ctx["is_founder"] = bool(getattr(u, "is_founder_admin", False))
        ctx["pending_admin_request_count"] = (
            AdminRequest.objects.filter(status=AdminRequest.Status.PENDING).count()
            if role == "admin"
            else 0
        )
        today = timezone.localdate()
        semesters = list(Semester.objects.filter(is_active=True))
        ctx["any_add_drop_open"] = any(is_within_add_drop(s, today) for s in semesters)

        if role == "student":
            try:
                sp = u.student_profile
                ctx["student_enrollment_active"] = Enrollment.objects.filter(
                    student=sp,
                    status__in=(Enrollment.Status.ENROLLED, Enrollment.Status.PENDING),
                ).count()
                ctx["student_next_step"] = (
                    _("Ders bırakma / ekleme penceresi açıkken kayıtlarınızı kontrol edin.")
                    if ctx["any_add_drop_open"]
                    else _("Pencere kapalıysa transkriptinizi kontrol edip sonraki dönem için plan yapın.")
                )
            except Exception:
                ctx["student_enrollment_active"] = None
                ctx["student_next_step"] = _(
                    "Profiliniz eksik görünüyor. Öğrenci işlerinizle iletişime geçin."
                )

        if role == "instructor":
            try:
                inst = u.instructor_profile
                ctx["instructor_pending_grades"] = (
                    Enrollment.objects.filter(
                        section__offering__instructor=inst,
                        status=Enrollment.Status.ENROLLED,
                    )
                    .filter(
                        Q(academic_grade__isnull=True) | Q(academic_grade__letter_grade="")
                    )
                    .count()
                )
                ctx["instructor_offering_count"] = CourseOffering.objects.filter(
                    instructor=inst, is_active=True
                ).count()
            except Exception:
                ctx["instructor_pending_grades"] = None
                ctx["instructor_offering_count"] = None

        if role == "admin":
            ctx["recent_announcements"] = list(
                Announcement.objects.filter(is_active=True).order_by("-created_at")[:3]
            )
            ctx["recent_critical_events"] = list(
                AuditLog.objects.select_related("actor")
                .filter(
                    event_type__in=[
                        "admin_request_approved",
                        "admin_request_rejected",
                        "enrollment_created",
                        "enrollment_status_changed",
                        "grade_entry",
                    ]
                )
                .order_by("-created_at")[:5]
            )

        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Pano"), "url": None},
        )
        return ctx


class AdminRequestQueueView(FounderAdminRequiredMixin, ListView):
    model = AdminRequest
    template_name = "dashboard/admin_request_list.html"
    context_object_name = "admin_requests"
    paginate_by = 25

    def get_queryset(self):
        return (
            AdminRequest.objects.filter(status=AdminRequest.Status.PENDING)
            .select_related("user")
            .order_by("created_at")
        )


class _AdminRequestDecisionView(FounderAdminRequiredMixin, View):
    success_message = ""

    def post(self, request, pk, *args, **kwargs):
        raise NotImplementedError


class AdminRequestApproveView(_AdminRequestDecisionView):
    def post(self, request, pk, *args, **kwargs):
        with transaction.atomic():
            req = (
                AdminRequest.objects.select_for_update()
                .filter(pk=pk)
                .select_related("user")
                .first()
            )
            if not req:
                messages.error(request, _("Talep bulunamadı."))
                return redirect("dashboard:admin_requests")
            if req.status != AdminRequest.Status.PENDING:
                messages.info(request, _("Bu talep zaten işlendi."))
                return redirect("dashboard:admin_requests")

            target = User.objects.select_for_update().get(pk=req.user_id)
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.status = AdminRequest.Status.APPROVED
            req.save(update_fields=["status", "reviewed_by", "reviewed_at"])

            if target.role != User.Role.ADMIN:
                target.role = User.Role.ADMIN
                target.save(update_fields=["role"])

            log_event(
                event_type="admin_request_approved",
                actor=request.user,
                target_type="accounts.AdminRequest",
                target_id=str(req.pk),
                metadata={
                    "target_user_id": target.pk,
                    "target_username": target.username,
                },
                request=request,
            )

        messages.success(request, _("Talep onaylandı; kullanıcıya yönetici rolü verildi."))
        return redirect("dashboard:admin_requests")


class AdminRequestRejectView(_AdminRequestDecisionView):
    def post(self, request, pk, *args, **kwargs):
        with transaction.atomic():
            req = AdminRequest.objects.select_for_update().filter(pk=pk).first()
            if not req:
                messages.error(request, _("Talep bulunamadı."))
                return redirect("dashboard:admin_requests")
            if req.status != AdminRequest.Status.PENDING:
                messages.info(request, _("Bu talep zaten işlendi."))
                return redirect("dashboard:admin_requests")

            req.status = AdminRequest.Status.REJECTED
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.save(update_fields=["status", "reviewed_by", "reviewed_at"])

            log_event(
                event_type="admin_request_rejected",
                actor=request.user,
                target_type="accounts.AdminRequest",
                target_id=str(req.pk),
                metadata={"target_user_id": req.user_id},
                request=request,
            )

        messages.success(request, _("Talep reddedildi."))
        return redirect("dashboard:admin_requests")


# ---------------------------------------------------------------------------
# Öğrenci / Akademisyen onay kuyruğu
# ---------------------------------------------------------------------------

class UserApprovalQueueView(LoginRequiredMixin, ListView):
    """Onay bekleyen öğrenci ve akademisyen listesi — yalnızca admin."""
    template_name = "dashboard/user_approval_list.html"
    context_object_name = "pending_students"
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "admin":
            messages.error(request, _("Bu sayfaya erişim yetkiniz yok."))
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            StudentProfile.objects.filter(is_approved=False)
            .select_related("user", "department")
            .order_by("created_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["pending_instructors"] = (
            InstructorProfile.objects.filter(is_approved=False)
            .select_related("user", "department")
            .order_by("created_at")
        )
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Pano"), "url": reverse("dashboard:index")},
            {"label": _("Kullanıcı onayları"), "url": None},
        )
        return ctx


class ApproveStudentView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "admin":
            messages.error(request, _("Bu işlem için yetkiniz yok."))
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk, *args, **kwargs):
        profile = StudentProfile.objects.filter(pk=pk).select_related("user").first()
        if not profile:
            messages.error(request, _("Öğrenci profili bulunamadı."))
            return redirect("dashboard:user_approvals")


class StatisticsView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/statistics.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "admin":
            messages.error(request, _("Bu sayfaya erişim yetkiniz yok."))
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from students.models import StudentProfile
        from courses.models import Course
        from academic.models import Program
        from enrollments.models import Enrollment
        from instructors.models import InstructorProfile

        ctx = super().get_context_data(**kwargs)

        ctx["total_students"] = StudentProfile.objects.count()
        ctx["approved_students"] = StudentProfile.objects.filter(is_approved=True).count()
        ctx["total_instructors"] = InstructorProfile.objects.filter(is_approved=True).count()
        ctx["total_active_courses"] = Course.objects.filter(is_active=True).count()

        status_counts = list(
            Enrollment.objects.values("status").annotate(count=Count("id")).order_by("status")
        )
        total_enrollments = sum(r["count"] for r in status_counts) or 1
        ctx["total_enrollments"] = total_enrollments

        status_map = {r["status"]: r["count"] for r in status_counts}
        ctx["enrollment_status_rows"] = [
            {"label": _("Kayıtlı"), "status": "enrolled", "count": status_map.get("enrolled", 0), "color": "emerald"},
            {"label": _("Beklemede"), "status": "pending", "count": status_map.get("pending", 0), "color": "amber"},
            {"label": _("Tamamlandı"), "status": "completed", "count": status_map.get("completed", 0), "color": "indigo"},
            {"label": _("Bırakıldı"), "status": "dropped", "count": status_map.get("dropped", 0), "color": "rose"},
            {"label": _("Çekildi"), "status": "withdrawn", "count": status_map.get("withdrawn", 0), "color": "slate"},
        ]
        for row in ctx["enrollment_status_rows"]:
            row["pct"] = round(row["count"] / total_enrollments * 100)

        ctx["top_courses"] = list(
            Enrollment.objects
            .filter(status__in=("enrolled", "pending", "completed"))
            .values("section__offering__course__code", "section__offering__course__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        ctx["students_per_program"] = list(
            StudentProfile.objects
            .filter(program__isnull=False)
            .values("program__code", "program__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        ctx["students_per_dept"] = list(
            StudentProfile.objects
            .filter(department__isnull=False)
            .values("department__code", "department__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:8]
        )

        ctx["pending_student_approvals"] = StudentProfile.objects.filter(is_approved=False).count()
        ctx["pending_enrollments"] = Enrollment.objects.filter(status=Enrollment.Status.PENDING).count()

        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Pano"), "url": reverse("dashboard:index")},
            {"label": _("İstatistikler"), "url": None},
        )
        return ctx
        action = request.POST.get("action", "approve")
        if action == "reject":
            profile.user.is_active = False
            profile.user.save(update_fields=["is_active"])
            messages.warning(request, f"{profile.user.get_full_name() or profile.user.username} reddedildi ve hesap devre dışı bırakıldı.")
        else:
            profile.is_approved = True
            profile.save(update_fields=["is_approved"])
            messages.success(request, f"{profile.user.get_full_name() or profile.user.username} onaylandı.")
        log_event(
            event_type="user_approval_decision",
            actor=request.user,
            target_type="students.StudentProfile",
            target_id=str(profile.pk),
            metadata={"action": action, "username": profile.user.username},
            request=request,
        )
        return redirect("dashboard:user_approvals")


class ApproveInstructorView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "admin":
            messages.error(request, _("Bu işlem için yetkiniz yok."))
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk, *args, **kwargs):
        profile = InstructorProfile.objects.filter(pk=pk).select_related("user").first()
        if not profile:
            messages.error(request, _("Akademisyen profili bulunamadı."))
            return redirect("dashboard:user_approvals")
        action = request.POST.get("action", "approve")
        if action == "reject":
            profile.user.is_active = False
            profile.user.save(update_fields=["is_active"])
            messages.warning(request, f"{profile.user.get_full_name() or profile.user.username} reddedildi ve hesap devre dışı bırakıldı.")
        else:
            profile.is_approved = True
            profile.save(update_fields=["is_approved"])
            messages.success(request, f"{profile.user.get_full_name() or profile.user.username} onaylandı.")
        log_event(
            event_type="user_approval_decision",
            actor=request.user,
            target_type="instructors.InstructorProfile",
            target_id=str(profile.pk),
            metadata={"action": action, "username": profile.user.username},
            request=request,
        )
        return redirect("dashboard:user_approvals")


class StatisticsView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/statistics.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "admin":
            messages.error(request, _("Bu sayfaya erişim yetkiniz yok."))
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from students.models import StudentProfile
        from courses.models import Course
        from enrollments.models import Enrollment
        from instructors.models import InstructorProfile

        ctx = super().get_context_data(**kwargs)

        ctx["total_students"] = StudentProfile.objects.count()
        ctx["approved_students"] = StudentProfile.objects.filter(is_approved=True).count()
        ctx["total_instructors"] = InstructorProfile.objects.filter(is_approved=True).count()
        ctx["total_active_courses"] = Course.objects.filter(is_active=True).count()

        status_counts = list(
            Enrollment.objects.values("status").annotate(count=Count("id")).order_by("status")
        )
        raw_total = sum(r["count"] for r in status_counts)
        ctx["total_enrollments"] = raw_total
        divisor = raw_total or 1

        status_map = {r["status"]: r["count"] for r in status_counts}
        ctx["enrollment_status_rows"] = [
            {"label": _("Kayıtlı"), "status": "enrolled", "count": status_map.get("enrolled", 0), "color": "emerald"},
            {"label": _("Beklemede"), "status": "pending", "count": status_map.get("pending", 0), "color": "amber"},
            {"label": _("Tamamlandı"), "status": "completed", "count": status_map.get("completed", 0), "color": "indigo"},
            {"label": _("Bırakıldı"), "status": "dropped", "count": status_map.get("dropped", 0), "color": "rose"},
            {"label": _("Çekildi"), "status": "withdrawn", "count": status_map.get("withdrawn", 0), "color": "slate"},
        ]
        for row in ctx["enrollment_status_rows"]:
            row["pct"] = round(row["count"] / divisor * 100)

        ctx["top_courses"] = list(
            Enrollment.objects
            .filter(status__in=("enrolled", "pending", "completed"))
            .values("section__offering__course__code", "section__offering__course__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        ctx["students_per_program"] = list(
            StudentProfile.objects
            .filter(program__isnull=False)
            .values("program__code", "program__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        ctx["students_per_dept"] = list(
            StudentProfile.objects
            .filter(department__isnull=False)
            .values("department__code", "department__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:8]
        )

        ctx["pending_student_approvals"] = StudentProfile.objects.filter(is_approved=False).count()
        ctx["pending_enrollments"] = Enrollment.objects.filter(status=Enrollment.Status.PENDING).count()

        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Pano"), "url": reverse("dashboard:index")},
            {"label": _("İstatistikler"), "url": None},
        )
        return ctx
