from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import ListView, UpdateView

from core.breadcrumbs import home, items
from core.permissions import AdminRequiredMixin, InstructorRequiredMixin

from .forms import InstructorAssignForm
from .models import InstructorProfile


class InstructorHomeView(InstructorRequiredMixin, View):
    template_name = "instructors/index.html"

    def get(self, request):
        from courses.models import CourseOffering
        from enrollments.models import Enrollment

        try:
            profile = request.user.instructor_profile
        except ObjectDoesNotExist:
            profile = None

        offering_count = 0
        pending_grades = 0
        pending_advisees = 0

        if profile:
            offering_count = CourseOffering.objects.filter(
                instructor=profile, is_active=True
            ).count()
            pending_grades = (
                Enrollment.objects.filter(
                    section__offering__instructor=profile,
                    status=Enrollment.Status.ENROLLED,
                )
                .filter(Q(academic_grade__isnull=True) | Q(academic_grade__letter_grade=""))
                .count()
            )
            pending_advisees = Enrollment.objects.filter(
                student__advisor=profile,
                status=Enrollment.Status.PENDING,
            ).count()

        return render(request, self.template_name, {
            "profile": profile,
            "offering_count": offering_count,
            "pending_grades": pending_grades,
            "pending_advisees": pending_advisees,
        })


class InstructorAdminListView(AdminRequiredMixin, ListView):
    model = InstructorProfile
    template_name = "instructors/admin_list.html"
    context_object_name = "instructors"
    paginate_by = 30

    def get_queryset(self):
        qs = InstructorProfile.objects.select_related("user", "department")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(employee_no__icontains=q)
                | Q(user__first_name__icontains=q)
                | Q(user__last_name__icontains=q)
                | Q(user__username__icontains=q)
            )
        dept = (self.request.GET.get("dept") or "").strip()
        if dept.isdigit():
            qs = qs.filter(department_id=int(dept))
        approved = self.request.GET.get("approved", "")
        if approved == "1":
            qs = qs.filter(is_approved=True)
        elif approved == "0":
            qs = qs.filter(is_approved=False)
        return qs.order_by("employee_no")

    def get_context_data(self, **kwargs):
        from academic.models import Department
        ctx = super().get_context_data(**kwargs)
        ctx["current_filters"] = {
            "q": self.request.GET.get("q", "").strip(),
            "dept": self.request.GET.get("dept", ""),
            "approved": self.request.GET.get("approved", ""),
        }
        ctx["departments"] = Department.objects.filter(is_active=True).order_by("code")
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Akademisyen yönetimi"), "url": None},
        )
        return ctx


class InstructorAdminEditView(AdminRequiredMixin, UpdateView):
    model = InstructorProfile
    form_class = InstructorAssignForm
    template_name = "instructors/admin_form.html"
    success_url = reverse_lazy("instructors:admin_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            _("%(no)s sicil numaralı akademisyenin bilgileri güncellendi.") % {
                "no": self.object.employee_no
            },
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Akademisyen yönetimi"), "url": reverse("instructors:admin_list")},
            {"label": _("Düzenle"), "url": None},
        )
        return ctx
