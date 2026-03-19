from django.contrib import admin

from .models import InstructorProfile


@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ("employee_no", "user", "department", "title", "is_active")
    search_fields = ("employee_no", "user__username", "user__email")
    list_filter = ("department", "is_active")
    ordering = ("employee_no",)
