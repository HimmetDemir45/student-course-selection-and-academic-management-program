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
            "numeric_grade": "Sayisal not",
        }
