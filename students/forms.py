from django import forms
from django.utils.translation import gettext_lazy as _

from .models import StudentProfile


class StudentAssignForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ("department", "program", "enrollment_year", "advisor", "is_approved")
        labels = {
            "department": _("Bölüm"),
            "program": _("Program"),
            "enrollment_year": _("Kayıt yılı"),
            "advisor": _("Danışman"),
            "is_approved": _("Hesap onaylı"),
        }
        help_texts = {
            "enrollment_year": _("Öğrencinin sisteme kayıt yılı (ör. 2024)"),
            "is_approved": _("Onaylı öğrenciler ders seçimi yapabilir."),
        }
