from django import forms

from .models import Announcement, Department, Grade


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ("code", "name", "description", "is_active")


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ("title", "body", "semester", "department", "target_role", "is_active")


class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ("letter_grade", "numeric_grade")
        labels = {
            "letter_grade": "Harf notu",
            "numeric_grade": "Sayısal not",
        }
        help_texts = {
            "letter_grade": "A, B, C, D veya F (büyük harf önerilir).",
            "numeric_grade": "İsteğe bağlı; harf notu ile birlikte kullanılabilir.",
        }
        widgets = {
            "letter_grade": forms.TextInput(
                attrs={"class": "form-control", "maxlength": "2", "autocomplete": "off"}
            ),
            "numeric_grade": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }
