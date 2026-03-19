from django.contrib import admin

from .models import Classroom, Course, CourseOffering, CoursePrerequisite


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "department", "program", "credits", "is_active")
    search_fields = ("code", "name", "department__name")
    list_filter = ("department", "program", "is_active")
    ordering = ("code",)


@admin.register(CoursePrerequisite)
class CoursePrerequisiteAdmin(admin.ModelAdmin):
    list_display = ("course", "prerequisite", "created_at")
    search_fields = ("course__code", "prerequisite__code")
    list_filter = ("course__department",)
    ordering = ("course__code",)


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ("building", "room_number", "capacity", "is_active")
    search_fields = ("building", "room_number")
    list_filter = ("building", "is_active")
    ordering = ("building", "room_number")


@admin.register(CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    list_display = ("course", "semester", "section", "instructor", "classroom", "quota", "is_active")
    search_fields = ("course__code", "course__name", "section", "instructor__user__username")
    list_filter = ("semester", "is_active", "course__department")
    ordering = ("-semester__academic_year", "course__code", "section")
