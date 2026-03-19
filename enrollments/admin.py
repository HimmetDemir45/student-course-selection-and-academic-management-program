from django.contrib import admin

from .models import Enrollment, Grade


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "offering", "status", "created_at")
    search_fields = ("student__student_no", "offering__course__code")
    list_filter = ("status", "offering__semester")
    ordering = ("-created_at",)


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "letter_grade", "numeric_grade", "created_at")
    search_fields = ("enrollment__student__student_no", "enrollment__offering__course__code")
    list_filter = ("letter_grade",)
    ordering = ("-created_at",)
