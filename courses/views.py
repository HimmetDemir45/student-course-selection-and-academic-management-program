from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from academic.models import Department
from core.permissions import AdminRequiredMixin

from .forms import CourseForm, CourseOfferingForm
from .models import Course, CourseOffering


class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = "courses/course_list.html"
    context_object_name = "courses"

    def get_queryset(self):
        qs = Course.objects.select_related("department", "program")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))
        dep = self.request.GET.get("department")
        if dep and str(dep).isdigit():
            qs = qs.filter(department_id=int(dep))
        sort = self.request.GET.get("sort") or "code"
        if sort == "name":
            qs = qs.order_by("name", "code")
        elif sort == "dept":
            qs = qs.order_by("department__code", "code")
        elif sort == "credits_desc":
            qs = qs.order_by("-credits", "code")
        else:
            qs = qs.order_by("code")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter_departments"] = Department.objects.filter(is_active=True).order_by("code")
        ctx["current_filters"] = {
            "q": self.request.GET.get("q", "").strip(),
            "department": self.request.GET.get("department", ""),
            "sort": self.request.GET.get("sort", "code"),
        }
        return ctx


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
