from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from core.services.cached_stats import cached_active_offering_count

from .permissions import role_required


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
    return render(
        request,
        "core/home.html",
        {"active_offering_count": cached_active_offering_count()},
    )


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
