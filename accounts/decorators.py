"""Rol tabanli decorator ve mixin'lerin accounts modulunden erisimi (tanimlar core.permissions)."""

from core.permissions import (  # noqa: F401
    AdminRequiredMixin,
    InstructorRequiredMixin,
    RoleRequiredMixin,
    StudentRequiredMixin,
    role_required,
)
