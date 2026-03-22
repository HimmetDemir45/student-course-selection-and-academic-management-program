from django.contrib import admin

from .models import (
    Announcement,
    CourseSection,
    Department,
    Grade,
    GradeItem,
    Program,
    SectionTimeSlot,
    Semester,
    Transcript,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "created_at")
    search_fields = ("code", "name")
    list_filter = ("is_active",)
    ordering = ("name",)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "department", "degree_level", "is_active")
    search_fields = ("code", "name", "department__name")
    list_filter = ("degree_level", "department", "is_active")
    ordering = ("name",)


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = (
        "academic_year",
        "term",
        "start_date",
        "end_date",
        "add_drop_start",
        "add_drop_end",
        "is_active",
    )
    search_fields = ("academic_year", "name")
    list_filter = ("term", "is_active")
    ordering = ("-academic_year", "term")


@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    list_display = ("student", "semester", "gpa", "total_credits", "created_at")
    search_fields = ("student__student_no", "student__user__username")
    list_filter = ("semester",)
    ordering = ("-created_at",)


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = ("offering", "max_enrollment", "is_active")
    list_filter = ("is_active",)
    search_fields = ("offering__course__code", "offering__section")


@admin.register(SectionTimeSlot)
class SectionTimeSlotAdmin(admin.ModelAdmin):
    list_display = ("section", "weekday", "start_time", "end_time")
    list_filter = ("weekday",)


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "letter_grade", "numeric_grade", "updated_at")
    search_fields = ("enrollment__student__student_no",)


@admin.register(GradeItem)
class GradeItemAdmin(admin.ModelAdmin):
    list_display = ("grade", "label", "weight", "score")


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "target_role", "semester", "department", "is_active", "created_at")
    search_fields = ("title", "body")
    list_filter = ("target_role", "semester", "department", "is_active")
    ordering = ("-created_at",)
