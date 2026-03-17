from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from .permissions import role_required


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
