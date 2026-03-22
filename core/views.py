from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

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
    return render(request, "core/home.html")


@login_required
@role_required("student")
def student_test_page(request):
    return HttpResponse("Student-only test page")


@login_required
@role_required("instructor")
def instructor_test_page(request):
    return HttpResponse("Instructor-only test page")
