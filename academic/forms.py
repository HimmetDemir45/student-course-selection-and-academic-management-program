from django import forms

from .models import Announcement, Department


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ("code", "name", "description", "is_active")


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ("title", "body", "semester", "department", "target_role", "is_active")
