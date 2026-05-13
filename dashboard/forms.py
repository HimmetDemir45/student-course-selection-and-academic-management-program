from django import forms
from academic.models import Semester
from students.models import StudentProfile
from academic.models import Department, Program
from instructors.models import InstructorProfile


class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ["name", "academic_year", "term", "start_date", "end_date", "add_drop_start", "add_drop_end", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "akd-input"}),
            "academic_year": forms.TextInput(attrs={"class": "akd-input"}),
            "term": forms.Select(attrs={"class": "akd-input"}),
            "start_date": forms.DateInput(attrs={"class": "akd-input", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "akd-input", "type": "date"}),
            "add_drop_start": forms.DateInput(attrs={"class": "akd-input", "type": "date"}),
            "add_drop_end": forms.DateInput(attrs={"class": "akd-input", "type": "date"}),
            "is_active": forms.CheckboxInput(attrs={"class": "akd-checkbox"}),
        }


class StudentAssignmentForm(forms.ModelForm):
    """
    Yönetici tarafından öğrenci sınıf ve programa atanması için form.
    """
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label="Bölüm",
        widget=forms.Select(attrs={"class": "akd-input"}),
    )
    program = forms.ModelChoiceField(
        queryset=Program.objects.none(),
        required=False,
        label="Program",
        widget=forms.Select(attrs={"class": "akd-input"}),
    )
    advisor = forms.ModelChoiceField(
        queryset=InstructorProfile.objects.filter(is_approved=True),
        required=False,
        label="Danışman",
        widget=forms.Select(attrs={"class": "akd-input"}),
    )

    class Meta:
        model = StudentProfile
        fields = ["department", "program", "enrollment_year", "advisor", "is_approved"]
        widgets = {
            "enrollment_year": forms.NumberInput(attrs={"class": "akd-input", "min": "1", "max": "4"}),
            "is_approved": forms.CheckboxInput(attrs={"class": "akd-checkbox"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Program dropdown'u dinamik olarak doldur
        if self.instance.department:
            self.fields["program"].queryset = Program.objects.filter(
                department=self.instance.department
            )
        elif self.data:
            try:
                dept_id = int(self.data.get("department"))
                self.fields["program"].queryset = Program.objects.filter(department_id=dept_id)
            except (ValueError, TypeError):
                pass

    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get("department")
        program = cleaned_data.get("program")

        if program and program.department != department:
            raise forms.ValidationError("Seçilen program bu bölüme ait değil.")

        return cleaned_data
