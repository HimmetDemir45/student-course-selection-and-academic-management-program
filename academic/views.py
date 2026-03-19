from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.permissions import AdminRequiredMixin

from .forms import AnnouncementForm, DepartmentForm
from .models import Announcement, Department


class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = "academic/department_list.html"
    context_object_name = "departments"


class DepartmentCreateView(AdminRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = "academic/department_form.html"
    success_url = reverse_lazy("academic:department_list")


class DepartmentUpdateView(AdminRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = "academic/department_form.html"
    success_url = reverse_lazy("academic:department_list")


class DepartmentDeleteView(AdminRequiredMixin, DeleteView):
    model = Department
    template_name = "academic/department_confirm_delete.html"
    success_url = reverse_lazy("academic:department_list")


class AnnouncementListView(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = "academic/announcement_list.html"
    context_object_name = "announcements"

    def get_queryset(self):
        qs = Announcement.objects.select_related("semester", "department", "published_by")
        user = self.request.user
        if user.role == "admin":
            return qs

        role_filter = Q(target_role="all") | Q(target_role=user.role)
        return qs.filter(is_active=True).filter(role_filter)


class AnnouncementCreateView(AdminRequiredMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = "academic/announcement_form.html"
    success_url = reverse_lazy("academic:announcement_list")

    def form_valid(self, form):
        form.instance.published_by = self.request.user
        return super().form_valid(form)


class AnnouncementUpdateView(AdminRequiredMixin, UpdateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = "academic/announcement_form.html"
    success_url = reverse_lazy("academic:announcement_list")


class AnnouncementDeleteView(AdminRequiredMixin, DeleteView):
    model = Announcement
    template_name = "academic/announcement_confirm_delete.html"
    success_url = reverse_lazy("academic:announcement_list")
