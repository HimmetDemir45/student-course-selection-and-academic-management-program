"""
Rol bazlı view mixin'leri: AdminRequiredMixin, StudentRequiredMixin, InstructorRequiredMixin, FounderAdminRequiredMixin.
"""
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

    def dispatch(self, request, *args, **kwargs):
        # Onay kontrolü super()'dan ÖNCE yapılmalı; aksi hâlde view post() metodu
        # (ör. enrollment kaydı) çalıştıktan sonra redirect döner ama DB yazımı
        # zaten gerçekleşmiş olur.
        if request.user.is_authenticated and request.user.role == "student":
            profile = getattr(request.user, "student_profile", None)
            if profile is not None and not profile.is_approved:
                messages.warning(
                    request,
                    "Hesabınız henüz yönetici tarafından onaylanmadı. "
                    "Onaylandıktan sonra bu alana erişebilirsiniz.",
                )
                return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)


class InstructorRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("instructor", "admin")

    def dispatch(self, request, *args, **kwargs):
        # Onay kontrolü super()'dan ÖNCE — StudentRequiredMixin ile aynı gerekçe.
        if request.user.is_authenticated and request.user.role == "instructor":
            profile = getattr(request.user, "instructor_profile", None)
            if profile is not None and not profile.is_approved:
                messages.warning(
                    request,
                    "Hesabınız henüz yönetici tarafından onaylanmadı. "
                    "Onaylandıktan sonra bu alana erişebilirsiniz.",
                )
                return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)


class FounderAdminRequiredMixin(LoginRequiredMixin):
    """Kurucu yönetici (is_founder_admin) için; yetkisizde 403."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not getattr(request.user, "is_founder_admin", False):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
