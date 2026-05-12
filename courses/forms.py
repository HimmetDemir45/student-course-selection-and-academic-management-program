from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Classroom, Course, CourseOffering


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
        widgets = {
            "department": forms.Select(attrs={"class": "form-select"}),
            "program": forms.Select(attrs={"class": "form-select"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "credits": forms.NumberInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control"}),
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
        widgets = {
            "course": forms.Select(attrs={"class": "form-select"}),
            "semester": forms.Select(attrs={"class": "form-select"}),
            "instructor": forms.Select(attrs={"class": "form-select"}),
            "classroom": forms.Select(attrs={"class": "form-select"}),
            "section": forms.TextInput(attrs={"class": "form-control"}),
            "quota": forms.NumberInput(attrs={"class": "form-control"}),
        }
