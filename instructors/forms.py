"""
Akademisyen profil ve admin yönetim form'ları.
"""
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import InstructorProfile


class InstructorAssignForm(forms.ModelForm):
    class Meta:
        model = InstructorProfile
        fields = ("department", "title", "is_approved")
        labels = {
            "department": _("Bölüm"),
            "title": _("Unvan"),
            "is_approved": _("Hesap onaylı"),
        }
        help_texts = {
            "title": _("Örn: Dr., Doç. Dr., Prof. Dr."),
            "is_approved": _("Onaylı akademisyenler sistemi tam kapasiteyle kullanabilir."),
        }
        widgets = {
            "title": forms.TextInput(attrs={"class": "akd-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply akd-input class to all non-checkbox widgets
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "akd-input")
