"""
StudentProfile için admin paneli (onay, danışman ataması, bölüm/program).
"""
from django.contrib import admin

from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("student_no", "user", "department", "program", "enrollment_year", "is_active")
    search_fields = ("student_no", "user__username", "user__email")
    list_filter = ("department", "program", "enrollment_year", "is_active")
    ordering = ("student_no",)
