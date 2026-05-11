from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Course, CourseOffering


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
