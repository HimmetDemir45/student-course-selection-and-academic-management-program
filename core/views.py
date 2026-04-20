from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from academic.models import Semester
from core.services.cached_stats import cached_active_offering_count
from core.services.enrollment_rules import is_within_add_drop
from enrollments.models import Enrollment

from .permissions import role_required


def _home_extra_context(request):
    """Ana sayfa rol kartları. Rollback: home() içindeki çağrıyı kaldırın."""
    if not request.user.is_authenticated:
        return {}
    u = request.user
    role = getattr(u, "role", None)
    today = timezone.localdate()
    semesters = list(Semester.objects.filter(is_active=True))
    ctx = {
        "home_any_add_drop_open": any(is_within_add_drop(s, today) for s in semesters),
    }
    if role == "student":
        try:
            sp = u.student_profile
            ctx["home_student_enrollments"] = Enrollment.objects.filter(
                student=sp,
                status__in=(Enrollment.Status.ENROLLED, Enrollment.Status.PENDING),
            ).count()
        except ObjectDoesNotExist:
            ctx["home_student_enrollments"] = None
    if role == "instructor":
        from django.db.models import Q

        from courses.models import CourseOffering

        try:
            inst = u.instructor_profile
            ctx["home_instructor_pending_grades"] = (
                Enrollment.objects.filter(
                    section__offering__instructor=inst,
                    status=Enrollment.Status.ENROLLED,
                )
                .filter(
                    Q(academic_grade__isnull=True) | Q(academic_grade__letter_grade="")
                )
                .count()
            )
            ctx["home_instructor_offerings"] = CourseOffering.objects.filter(
                instructor=inst, is_active=True
            ).count()
        except ObjectDoesNotExist:
            ctx["home_instructor_pending_grades"] = None
            ctx["home_instructor_offerings"] = None
    return ctx


@require_GET
def health_live(request):
    return JsonResponse({"status": "ok", "check": "live"})


@require_GET
def health_ready(request):
    try:
        connection.ensure_connection()
    except Exception:
        return JsonResponse(
            {"status": "unready", "database": "unavailable"},
            status=503,
        )
    return JsonResponse({"status": "ready", "database": "ok"})


def home(request):
    # See README "Performance checklist": cheap cached aggregate for dashboard-adjacent home context.
    ctx = {"active_offering_count": cached_active_offering_count()}
    ctx.update(_home_extra_context(request))
    return render(request, "core/home.html", ctx)


def handler403(request, exception=None):
    return render(request, "errors/403.html", status=403)


def handler404(request, exception=None):
    return render(request, "errors/404.html", status=404)


def handler500(request):
    return render(request, "errors/500.html", status=500)


@login_required
@role_required("student")
def student_test_page(request):
    return render(request, "core/student_test.html")


@login_required
@role_required("instructor")
def instructor_test_page(request):
    return render(request, "core/instructor_test.html")
