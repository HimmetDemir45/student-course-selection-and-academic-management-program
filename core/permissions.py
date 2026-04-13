from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Bu sayfaya erismek icin giris yapmalisiniz.")
                return redirect("accounts:login")

            if request.user.role not in allowed_roles:
                messages.error(request, "Bu alana erisim yetkiniz yok.")
                return redirect("core:home")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


class RoleRequiredMixin(AccessMixin):
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Bu sayfaya erismek icin giris yapmalisiniz.")
            return redirect("accounts:login")

        if request.user.role not in self.allowed_roles:
            messages.error(request, "Bu alana erisim yetkiniz yok.")
            return redirect("core:home")

        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("admin",)


class StudentRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("student",)


class InstructorRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("instructor", "admin")


class FounderAdminRequiredMixin(LoginRequiredMixin):
    """Kurucu yönetici (is_founder_admin) için; yetkisizde 403."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not getattr(request.user, "is_founder_admin", False):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
