from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from urllib.parse import urlparse

from academic.models import CourseSection, Department, Semester, SectionTimeSlot
from audit_logs.services import log_event
from core.breadcrumbs import home, items
from core.permissions import AdminRequiredMixin, role_required

from .forms import ClassroomForm, CourseForm, CourseOfferingForm, ElectivePoolForm
from .models import Classroom, Course, CourseOffering, CoursePrerequisite, ElectivePool


def _safe_referer(request, fallback: str) -> str:
    """Return HTTP_REFERER only when it points to the same host; otherwise return fallback."""
    referer = request.META.get("HTTP_REFERER", "")
    if referer:
        try:
            parsed = urlparse(referer)
            if not parsed.netloc or parsed.netloc == request.get_host():
                return referer
        except Exception:
            pass
    return fallback


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
    return redirect(_safe_referer(request, reverse("courses:course_list")))


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
    return redirect(_safe_referer(request, reverse("courses:offering_list")))


# ---------------------------------------------------------------------------
# Seçmeli Ders Havuzu CRUD
# ---------------------------------------------------------------------------

class ElectivePoolListView(AdminRequiredMixin, ListView):
    model = ElectivePool
    template_name = "courses/electivepool_list.html"
    context_object_name = "pools"
    paginate_by = 25

    def get_queryset(self):
        from academic.models import Program
        qs = ElectivePool.objects.select_related("program").prefetch_related("courses")
        prog = self.request.GET.get("program")
        if prog and str(prog).isdigit():
            qs = qs.filter(program_id=int(prog))
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(program__code__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        from academic.models import Program
        ctx = super().get_context_data(**kwargs)
        ctx["filter_programs"] = Program.objects.filter(is_active=True).order_by("code")
        ctx["current_filters"] = {
            "q": self.request.GET.get("q", "").strip(),
            "program": self.request.GET.get("program", ""),
        }
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Seçmeli ders havuzları"), "url": None},
        )
        return ctx


class ElectivePoolCreateView(AdminRequiredMixin, CreateView):
    model = ElectivePool
    form_class = ElectivePoolForm
    template_name = "courses/electivepool_form.html"
    success_url = reverse_lazy("courses:electivepool_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Seçmeli ders havuzları"), "url": reverse_lazy("courses:electivepool_list")},
            {"label": _("Yeni havuz"), "url": None},
        )
        return ctx


class ElectivePoolUpdateView(AdminRequiredMixin, UpdateView):
    model = ElectivePool
    form_class = ElectivePoolForm
    template_name = "courses/electivepool_form.html"
    success_url = reverse_lazy("courses:electivepool_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Seçmeli ders havuzları"), "url": reverse_lazy("courses:electivepool_list")},
            {"label": _("Havuz düzenle"), "url": None},
        )
        return ctx


class ElectivePoolDeleteView(AdminRequiredMixin, DeleteView):
    model = ElectivePool
    template_name = "courses/electivepool_confirm_delete.html"
    success_url = reverse_lazy("courses:electivepool_list")


# ---------------------------------------------------------------------------
# Derslik (Classroom) CRUD
# ---------------------------------------------------------------------------

class ClassroomListView(LoginRequiredMixin, ListView):
    model = Classroom
    template_name = "courses/classroom_list.html"
    context_object_name = "classrooms"
    paginate_by = 25

    def get_queryset(self):
        qs = Classroom.objects.all()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(building__icontains=q) | Q(room_number__icontains=q)
            )
        return qs.order_by("building", "room_number")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumb_items"] = items(
            home(),
            {"label": _("Derslikler"), "url": None},
        )
        ctx["current_filters"] = {"q": self.request.GET.get("q", "").strip()}
        return ctx


class ClassroomCreateView(AdminRequiredMixin, CreateView):
    model = Classroom
    form_class = ClassroomForm
    template_name = "courses/classroom_form.html"
    success_url = reverse_lazy("courses:classroom_list")


class ClassroomUpdateView(AdminRequiredMixin, UpdateView):
    model = Classroom
    form_class = ClassroomForm
    template_name = "courses/classroom_form.html"
    success_url = reverse_lazy("courses:classroom_list")


class ClassroomDeleteView(AdminRequiredMixin, DeleteView):
    model = Classroom
    template_name = "courses/classroom_confirm_delete.html"
    success_url = reverse_lazy("courses:classroom_list")


# ---------------------------------------------------------------------------
# Önkoşul Yönetimi (Prerequisite Management)
# ---------------------------------------------------------------------------

class CoursePrerequisiteView(AdminRequiredMixin, View):
    """GET: show a course's current prerequisites + an add form.
    POST: add or remove a prerequisite link."""

    template_name = "courses/prerequisite_manage.html"

    def _get_course(self, pk):
        return get_object_or_404(Course, pk=pk)

    def _context(self, course, error=None):
        existing_ids = list(
            course.prerequisite_links.values_list("prerequisite_id", flat=True)
        )
        available = (
            Course.objects
            .filter(is_active=True)
            .exclude(pk=course.pk)
            .exclude(pk__in=existing_ids)
            .order_by("code")
        )
        prereqs = (
            course.prerequisite_links
            .select_related("prerequisite", "prerequisite__department")
            .order_by("prerequisite__code")
        )
        return {
            "course": course,
            "prereqs": prereqs,
            "available_courses": available,
            "add_error": error,
            "breadcrumb_items": items(
                home(),
                {"label": _("Ders kataloğu"), "url": reverse("courses:course_list")},
                {"label": _("Önkoşullar"), "url": None},
            ),
        }

    def get(self, request, pk):
        course = self._get_course(pk)
        return render(request, self.template_name, self._context(course))

    def post(self, request, pk):
        course = self._get_course(pk)
        prereq_id = request.POST.get("prerequisite_id", "").strip()
        if not prereq_id or not str(prereq_id).isdigit():
            return render(request, self.template_name,
                          self._context(course, error=_("Geçerli bir ders seçin.")))

        prereq_id = int(prereq_id)
        if prereq_id == course.pk:
            return render(request, self.template_name,
                          self._context(course, error=_("Bir ders kendisinin önkoşulu olamaz.")))

        prereq_course = get_object_or_404(Course, pk=prereq_id)
        try:
            _, created = CoursePrerequisite.objects.get_or_create(
                course=course,
                prerequisite=prereq_course,
            )
        except IntegrityError:
            created = False

        if created:
            log_event(
                event_type="course.prerequisite_add",
                actor=request.user,
                target_type="courses.CoursePrerequisite",
                target_id=course.pk,
                metadata={"course": course.code, "prerequisite": prereq_course.code},
                request=request,
            )
            messages.success(
                request,
                _("'%(pre)s' dersi '%(course)s' dersine önkoşul olarak eklendi.") % {
                    "pre": prereq_course.code,
                    "course": course.code,
                },
            )
        else:
            messages.info(request, _("Bu önkoşul zaten tanımlı."))

        return redirect("courses:course_prerequisites", pk=course.pk)


# ---------------------------------------------------------------------------
# Ders Detay Sayfası
# ---------------------------------------------------------------------------

class CourseDetailView(LoginRequiredMixin, View):
    """Bir dersin tüm bilgilerini, önkoşullarını ve şube/zaman bilgilerini gösterir."""

    template_name = "courses/course_detail.html"

    def get(self, request, pk):
        course = get_object_or_404(
            Course.objects.select_related("department", "program"),
            pk=pk,
        )

        # Önkoşullar
        prerequisites = list(
            course.prerequisite_links
            .select_related("prerequisite__department")
            .order_by("prerequisite__code")
        )

        # Bu dersin önkoşulu olduğu dersler
        required_for = list(
            course.required_for_links
            .select_related("course__department")
            .order_by("course__code")
        )

        # Bu ders için aktif dönemlerdeki şubeler (zaman dilimleri dahil)
        offerings_qs = (
            CourseOffering.objects
            .filter(course=course, is_active=True)
            .select_related("semester", "instructor__user", "classroom")
            .order_by("-semester__academic_year", "semester__term", "section")
        )
        offerings_with_slots = []
        for off in offerings_qs:
            try:
                section = off.section_detail
                slots = list(
                    section.time_slots
                    .order_by("weekday", "start_time")
                )
            except Exception:
                section = None
                slots = []
            offerings_with_slots.append({
                "offering": off,
                "section": section,
                "slots": slots,
            })

        # Müfredattaki yeri (hangi programlar, hangi yıl/dönem)
        curriculum_items = list(
            course.curriculum_items
            .select_related("program__department")
            .order_by("program__code", "year_level", "term")
        )

        # Seçmeli havuzlar
        elective_pools = list(
            course.elective_pools
            .select_related("program")
            .order_by("program__code", "name")
        )

        _weekday_names = {
            0: "Pazartesi", 1: "Salı", 2: "Çarşamba",
            3: "Perşembe", 4: "Cuma", 5: "Cumartesi", 6: "Pazar",
        }

        ctx = {
            "course": course,
            "prerequisites": prerequisites,
            "required_for": required_for,
            "offerings_with_slots": offerings_with_slots,
            "curriculum_items": curriculum_items,
            "elective_pools": elective_pools,
            "weekday_names": _weekday_names,
            "breadcrumb_items": items(
                home(),
                {"label": _("Ders kataloğu"), "url": reverse("courses:course_list")},
                {"label": course.code, "url": None},
            ),
            "nav_namespace": "courses",
            "nav_url_name": "course_list",
        }
        return render(request, self.template_name, ctx)


@require_POST
@role_required("admin")
def prerequisite_delete(request, link_pk):
    link = get_object_or_404(CoursePrerequisite, pk=link_pk)
    course = link.course
    prereq = link.prerequisite
    link.delete()
    log_event(
        event_type="course.prerequisite_remove",
        actor=request.user,
        target_type="courses.CoursePrerequisite",
        target_id=course.pk,
        metadata={"course": course.code, "prerequisite": prereq.code},
        request=request,
    )
    messages.success(
        request,
        _("'%(pre)s' önkoşulu '%(course)s' dersinden kaldırıldı.") % {
            "pre": prereq.code,
            "course": course.code,
        },
    )
    return redirect("courses:course_prerequisites", pk=course.pk)


# ---------------------------------------------------------------------------
# Ders Detay Sayfası
# ---------------------------------------------------------------------------

class CourseDetailView(LoginRequiredMixin, View):
    """Bir dersin tüm bilgilerini, önkoşullarını ve şube/zaman bilgilerini gösterir."""

    template_name = "courses/course_detail.html"

    def get(self, request, pk):
        course = get_object_or_404(
            Course.objects.select_related("department", "program"),
            pk=pk,
        )

        # Önkoşullar
        prerequisites = list(
            course.prerequisite_links
            .select_related("prerequisite__department")
            .order_by("prerequisite__code")
        )

        # Bu dersin önkoşulu olduğu dersler
        required_for = list(
            course.required_for_links
            .select_related("course__department")
            .order_by("course__code")
        )

        # Bu ders için aktif dönemlerdeki şubeler (zaman dilimleri dahil)
        offerings_qs = (
            CourseOffering.objects
            .filter(course=course, is_active=True)
            .select_related("semester", "instructor__user", "classroom")
            .order_by("-semester__academic_year", "semester__term", "section")
        )
        offerings_with_slots = []
        for off in offerings_qs:
            try:
                section = off.section_detail
                slots = list(
                    section.time_slots.order_by("weekday", "start_time")
                )
            except Exception:
                section = None
                slots = []
            offerings_with_slots.append({
                "offering": off,
                "section": section,
                "slots": slots,
            })

        # Müfredattaki yeri (hangi programlar, hangi yıl/dönem)
        curriculum_items = list(
            course.curriculum_items
            .select_related("program__department")
            .order_by("program__code", "year_level", "term")
        )

        # Seçmeli havuzlar
        elective_pools = list(
            course.elective_pools
            .select_related("program")
            .order_by("program__code", "name")
        )

        _weekday_names = {
            0: "Pazartesi", 1: "Salı", 2: "Çarşamba",
            3: "Perşembe", 4: "Cuma", 5: "Cumartesi", 6: "Pazar",
        }

        ctx = {
            "course": course,
            "prerequisites": prerequisites,
            "required_for": required_for,
            "offerings_with_slots": offerings_with_slots,
            "curriculum_items": curriculum_items,
            "elective_pools": elective_pools,
            "weekday_names": _weekday_names,
            "breadcrumb_items": items(
                home(),
                {"label": _("Ders kataloğu"), "url": reverse("courses:course_list")},
                {"label": course.code, "url": None},
            ),
            "nav_namespace": "courses",
            "nav_url_name": "course_list",
        }
        return render(request, self.template_name, ctx)
