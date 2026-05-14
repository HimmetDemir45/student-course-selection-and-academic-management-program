"""
Enrollment modeli için admin paneli (kayıt durumu filtreleme ve toplu işlemler).
"""
from django.contrib import admin

from .models import Enrollment


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "section", "status", "created_at")
    search_fields = ("student__student_no", "section__offering__course__code")
    list_filter = ("status", "section__offering__semester")
    ordering = ("-created_at",)
