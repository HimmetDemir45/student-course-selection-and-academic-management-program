from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Announcement, CurriculumItem, Department, Grade, Program, Semester, SectionTimeSlot


def _apply_akd_input(form):
    """Apply akd-input class to all non-checkbox / non-multi-checkbox widgets."""
    for _name, field in form.fields.items():
        if not isinstance(
            field.widget,
            (forms.CheckboxInput, forms.CheckboxSelectMultiple, forms.RadioSelect),
        ):
            field.widget.attrs.setdefault("class", "akd-input")


class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = (
            "name",
            "academic_year",
            "term",
            "start_date",
            "end_date",
            "add_drop_start",
            "add_drop_end",
            "is_active",
        )
        labels = {
            "name": _("Dönem adı"),
            "academic_year": _("Akademik yıl"),
            "term": _("Yarıyıl"),
            "start_date": _("Başlangıç tarihi"),
            "end_date": _("Bitiş tarihi"),
            "add_drop_start": _("Ders ekleme/bırakma başlangıcı"),
            "add_drop_end": _("Ders ekleme/bırakma bitişi"),
            "is_active": _("Aktif"),
        }
        help_texts = {
            "academic_year": _("Örn: 2025-2026"),
            "add_drop_start": _("Boş bırakılırsa ekleme/bırakma tarihi kontrolü devre dışı kalır."),
        }
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date", "class": "akd-input"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "akd-input"}),
            "add_drop_start": forms.DateInput(attrs={"type": "date", "class": "akd-input"}),
            "add_drop_end": forms.DateInput(attrs={"type": "date", "class": "akd-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_akd_input(self)


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ("code", "name", "description", "is_active")
        labels = {
            "code": _("Bölüm kodu"),
            "name": _("Bölüm adı"),
            "description": _("Açıklama"),
            "is_active": _("Aktif"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_akd_input(self)


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ("department", "code", "name", "degree_level", "credits_required", "is_active")
        labels = {
            "department": _("Bölüm"),
            "code": _("Program kodu"),
            "name": _("Program adı"),
            "degree_level": _("Derece"),
            "credits_required": _("Gerekli AKTS"),
            "is_active": _("Aktif"),
        }
        help_texts = {
            "credits_required": _("Mezuniyet için gereken toplam AKTS kredisi (varsayılan: 240)."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_akd_input(self)


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ("title", "body", "semester", "department", "target_role", "is_active")
        labels = {
            "title": _("Başlık"),
            "body": _("İçerik"),
            "semester": _("Dönem"),
            "department": _("Bölüm"),
            "target_role": _("Hedef kitle"),
            "is_active": _("Aktif"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_akd_input(self)


class CurriculumItemForm(forms.ModelForm):
    class Meta:
        model = CurriculumItem
        fields = ("program", "course", "year_level", "term", "order")
        labels = {
            "program": _("Program"),
            "course": _("Ders"),
            "year_level": _("Yıl"),
            "term": _("Yarıyıl"),
            "order": _("Sıra"),
        }
        help_texts = {
            "year_level": _("1–4 arası bir değer girin."),
            "order": _("Aynı dönem içinde görüntüleme sırası (küçük = önce)."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_akd_input(self)


class SectionTimeSlotForm(forms.ModelForm):
    class Meta:
        model = SectionTimeSlot
        fields = ("weekday", "start_time", "end_time")
        labels = {
            "weekday": _("Gün"),
            "start_time": _("Başlangıç saati"),
            "end_time": _("Bitiş saati"),
        }
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "akd-input"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "akd-input"}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        if start and end and end <= start:
            raise ValidationError(_("Bitiş saati başlangıç saatinden sonra olmalıdır."))
        return cleaned


class GradeForm(forms.ModelForm):
    # Geçerli harf notları (KTÜ standart)
    VALID_LETTERS = {"AA", "BA", "BB", "CB", "CC", "DC", "DD", "FD", "FF", "I"}

    class Meta:
        model = Grade
        fields = ("letter_grade", "numeric_grade")
        labels = {
            "letter_grade": "Harf notu",
            "numeric_grade": "Sayısal not",
        }
        help_texts = {
            "letter_grade": "AA, BA, BB, CB, CC, DC, DD, FD, FF veya I (incomplete).",
            "numeric_grade": "İsteğe bağlı; 0-100 arası sayısal not.",
        }
        widgets = {
            "letter_grade": forms.TextInput(
                attrs={"class": "akd-input", "maxlength": "2", "autocomplete": "off",
                       "placeholder": "AA / BB / FF / I"}
            ),
            "numeric_grade": forms.NumberInput(attrs={"class": "akd-input", "step": "0.01",
                                                       "min": "0", "max": "100"}),
        }

    def clean_letter_grade(self):
        value = (self.cleaned_data.get("letter_grade") or "").strip().upper()
        if not value:
            return value
        if value not in self.VALID_LETTERS:
            raise forms.ValidationError(
                "Geçersiz harf notu. Geçerli olanlar: " + ", ".join(sorted(self.VALID_LETTERS))
            )
        return value

    def clean_numeric_grade(self):
        value = self.cleaned_data.get("numeric_grade")
        if value is None:
            return value
        if value < 0 or value > 100:
            raise forms.ValidationError("Sayısal not 0 ile 100 arasında olmalıdır.")
        return value
