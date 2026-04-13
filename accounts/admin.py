from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Rol ve kurucu", {"fields": ("role", "is_founder_admin")}),
    )
    list_display = ("username", "email", "first_name", "last_name", "role", "is_founder_admin", "is_staff")
    list_filter = ("role", "is_founder_admin", "is_staff", "is_superuser", "is_active")

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if "is_founder_admin" not in ro:
            ro.append("is_founder_admin")
        if not self._editor_is_founder(request):
            if obj and obj.role == User.Role.ADMIN and "role" not in ro:
                ro.append("role")
        return ro

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "role" and request.user.is_authenticated and not self._editor_is_founder(request):
            kwargs["choices"] = [c for c in User.Role.choices if c[0] != User.Role.ADMIN]
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    @staticmethod
    def _editor_is_founder(request) -> bool:
        u = request.user
        return bool(getattr(u, "is_authenticated", False) and getattr(u, "is_founder_admin", False))
