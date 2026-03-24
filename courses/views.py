from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.permissions import AdminRequiredMixin

from .forms import CourseForm, CourseOfferingForm
from .models import Course, CourseOffering


class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = "courses/course_list.html"
    context_object_name = "courses"

    def get_queryset(self):
        return Course.objects.select_related("department", "program").order_by("code")


class CourseCreateView(AdminRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = "courses/course_form.html"
    success_url = reverse_lazy("courses:course_list")


class CourseUpdateView(AdminRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = "courses/course_form.html"
    success_url = reverse_lazy("courses:course_list")


class CourseDeleteView(AdminRequiredMixin, DeleteView):
    model = Course
    template_name = "courses/course_confirm_delete.html"
    success_url = reverse_lazy("courses:course_list")


class CourseOfferingListView(LoginRequiredMixin, ListView):
    model = CourseOffering
    template_name = "courses/courseoffering_list.html"
    context_object_name = "offerings"

    def get_queryset(self):
        qs = CourseOffering.objects.select_related(
            "course",
            "semester",
            "instructor",
            "instructor__user",
            "classroom",
        )
        user = self.request.user
        if user.role == "admin":
            return qs
        if user.role == "instructor":
            try:
                profile = user.instructor_profile
            except ObjectDoesNotExist:
                profile = None
            if profile:
                return qs.filter(instructor=profile)
            return qs.none()
        return qs.filter(is_active=True)


class CourseOfferingCreateView(AdminRequiredMixin, CreateView):
    model = CourseOffering
    form_class = CourseOfferingForm
    template_name = "courses/courseoffering_form.html"
    success_url = reverse_lazy("courses:offering_list")


class CourseOfferingUpdateView(AdminRequiredMixin, UpdateView):
    model = CourseOffering
    form_class = CourseOfferingForm
    template_name = "courses/courseoffering_form.html"
    success_url = reverse_lazy("courses:offering_list")


class CourseOfferingDeleteView(AdminRequiredMixin, DeleteView):
    model = CourseOffering
    template_name = "courses/courseoffering_confirm_delete.html"
    success_url = reverse_lazy("courses:offering_list")
