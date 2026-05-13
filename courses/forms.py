from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Classroom, Course, CourseOffering, ElectivePool


def _apply_akd_input(form):
    """Apply akd-input class to all non-checkbox / non-multi-checkbox widgets."""
    for _name, field in form.fields.items():
        if not isinstance(
            field.widget,
            (forms.CheckboxInput, forms.CheckboxSelectMultiple, forms.RadioSelect),
        ):
            field.widget.attrs.setdefault("class", "akd-input")


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ("building", "room_number", "capacity", "is_active")
        labels = {
            "building": _("Bina"),
            "room_number": _("Oda / sınıf no"),
            "capacity": _("Kapasite"),
            "is_active": _("Aktif"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_akd_input(self)


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = (
            "department",
            "program",
            "code",
            "name",
            "credits",
            "description",
            "is_active",
        )
        labels = {
            "department": _("Bölüm"),
            "program": _("Program"),
            "code": _("Ders kodu"),
            "name": _("Ders adı"),
            "credits": _("Kredi"),
            "description": _("Açıklama"),
            "is_active": _("Aktif"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_akd_input(self)


class ElectivePoolForm(forms.ModelForm):
    class Meta:
        model = ElectivePool
        fields = ("program", "name", "description", "required_count", "courses", "is_active")
        labels = {
            "program": _("Program"),
            "name": _("Havuz adı"),
            "description": _("Açıklama"),
            "required_count": _("Seçilmesi gereken ders sayısı"),
            "courses": _("Havuzdaki dersler"),
            "is_active": _("Aktif"),
        }
        help_texts = {
            "required_count": _("Öğrencinin bu havuzdan tamamlaması gereken ders adedi."),
            "description": _("Öğrencilere gösterilecek kısa açıklama."),
        }
        widgets = {
            "courses": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_akd_input(self)


class CourseOfferingForm(forms.ModelForm):
    class Meta:
        model = CourseOffering
        fields = (
            "course",
            "semester",
            "instructor",
            "classroom",
            "section",
            "quota",
            "is_active",
        )
        labels = {
            "course": _("Ders"),
            "semester": _("Dönem"),
            "instructor": _("Öğretim görevlisi"),
            "classroom": _("Derslik"),
            "section": _("Şube"),
            "quota": _("Kontenjan"),
            "is_active": _("Aktif"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_akd_input(self)
