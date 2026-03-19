from django import forms

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
