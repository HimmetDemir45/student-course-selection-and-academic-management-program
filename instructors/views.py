from django.views.generic import TemplateView

from core.permissions import InstructorRequiredMixin


class InstructorHomeView(InstructorRequiredMixin, TemplateView):
    template_name = "instructors/index.html"
