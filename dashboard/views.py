from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import ListView, TemplateView

from accounts.models import AdminRequest, User
from core.breadcrumbs import home, items
from academic.models import Announcement, Semester
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
            if ctx["is_founder"]
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
            except Exception:
                ctx["student_enrollment_active"] = None

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
            )

        messages.success(request, _("Talep reddedildi."))
        return redirect("dashboard:admin_requests")
