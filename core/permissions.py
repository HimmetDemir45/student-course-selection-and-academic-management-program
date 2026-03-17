from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
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
