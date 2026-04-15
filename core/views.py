from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.http import HttpResponse, JsonResponse
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


def _html_error_page(title: str, body: str, status: int) -> HttpResponse:
    html = (
        "<!DOCTYPE html><html lang='tr'><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{title}</title>"
        "<link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css'>"
        "</head><body class='bg-light'><main class='container py-5 text-center'>"
        f"<h1 class='display-6'>{title}</h1><p class='lead'>{body}</p>"
        "<a class='btn btn-primary' href='/'>Ana sayfaya dön</a>"
        "</main></body></html>"
    )
    return HttpResponse(html, status=status, content_type="text/html; charset=utf-8")


def handler403(request, exception=None):
    return _html_error_page("403 — Erişim reddedildi", "Bu işlem için yetkiniz yok.", 403)


def handler404(request, exception=None):
    return _html_error_page(
        "404 — Sayfa bulunamadı",
        "Aradığınız sayfa bulunamadı veya taşınmış olabilir.",
        404,
    )


def handler500(request):
    return _html_error_page(
        "500 — Sunucu hatası",
        "Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin.",
        500,
    )


@login_required
@role_required("student")
def student_test_page(request):
    return render(request, "core/student_test.html")


@login_required
@role_required("instructor")
def instructor_test_page(request):
    return render(request, "core/instructor_test.html")
