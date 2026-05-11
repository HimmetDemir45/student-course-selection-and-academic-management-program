from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from academic.models import Department, Semester
from audit_logs.services import log_event
from core.breadcrumbs import home, items
from core.permissions import AdminRequiredMixin, role_required

from .forms import CourseForm, CourseOfferingForm
from .models import Course, CourseOffering


class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = "courses/course_list.html"
    context_object_name = "courses"
    paginate_by = 25

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
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Ders kataloğu"), "url": None},
        )
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
    paginate_by = 25

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
            pass
        elif user.role == "instructor":
            try:
                profile = user.instructor_profile
            except ObjectDoesNotExist:
                profile = None
            if profile:
                qs = qs.filter(instructor=profile)
            else:
                qs = qs.none()
        else:
            qs = qs.filter(is_active=True)
        rq = self.request.GET
        q = (rq.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(course__code__icontains=q) | Q(course__name__icontains=q))
        sem = rq.get("semester")
        if sem and str(sem).isdigit():
            qs = qs.filter(semester_id=int(sem))
        sort = rq.get("sort") or "code"
        if sort == "semester":
            qs = qs.order_by("-semester__academic_year", "semester__term", "course__code", "section")
        elif sort == "section":
            qs = qs.order_by("section", "course__code")
        else:
            qs = qs.order_by("course__code", "section")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter_semesters"] = Semester.objects.filter(is_active=True).order_by("-academic_year", "term")
        ctx["current_filters"] = {
            "q": self.request.GET.get("q", "").strip(),
            "semester": self.request.GET.get("semester", ""),
            "sort": self.request.GET.get("sort", "code"),
        }
        label = _("Verdiğim ders teklifleri") if self.request.user.role == "instructor" else _("Ders teklifleri")
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Pano"), "url": reverse("dashboard:index")},
            {"label": label, "url": None},
        )
        return ctx


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


@require_POST
@role_required("admin")
def course_toggle_active(request, pk):
    obj = get_object_or_404(Course, pk=pk)
    previous = obj.is_active
    obj.is_active = not previous
    obj.save(update_fields=["is_active", "updated_at"])
    log_event(
        event_type="course.toggle_active",
        actor=request.user,
        target_type="courses.Course",
        target_id=obj.pk,
        metadata={"from": previous, "to": obj.is_active, "code": obj.code},
        request=request,
    )
    messages.success(
        request,
        _("'%(code)s — %(name)s' dersi %(state)s hale getirildi.") % {
            "code": obj.code,
            "name": obj.name,
            "state": _("aktif") if obj.is_active else _("pasif"),
        },
    )
    return redirect(request.META.get("HTTP_REFERER") or reverse("courses:course_list"))


@require_POST
@role_required("admin")
def offering_toggle_active(request, pk):
    obj = get_object_or_404(CourseOffering, pk=pk)
    previous = obj.is_active
    obj.is_active = not previous
    obj.save(update_fields=["is_active", "updated_at"])
    log_event(
        event_type="course_offering.toggle_active",
        actor=request.user,
        target_type="courses.CourseOffering",
        target_id=obj.pk,
        metadata={
            "from": previous,
            "to": obj.is_active,
            "course_code": obj.course.code,
            "section": obj.section,
        },
        request=request,
    )
    messages.success(
        request,
        _("'%(code)s / %(section)s' ders teklifi %(state)s hale getirildi.") % {
            "code": obj.course.code,
            "section": obj.section,
            "state": _("aktif") if obj.is_active else _("pasif"),
        },
    )
    return redirect(request.META.get("HTTP_REFERER") or reverse("courses:offering_list"))
