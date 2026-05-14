import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView as DjangoPasswordResetView
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST

from audit_logs.services import log_auth_event, log_event
from core.breadcrumbs import home, items

from .forms import AdminRequestForm, AkdPasswordChangeForm, LoginForm, ProfileForm, RegisterForm
from .models import AdminRequest, User
from .services.login_throttle import clear_login_throttle, login_throttle, register_login_failure

logger = logging.getLogger(__name__)


class LoggingPasswordResetView(DjangoPasswordResetView):
    """
    Django'nun PasswordResetView'ı, SMTP hatasında sessizce başarısız olur.
    Bu sınıf e-posta gönderim sürecini log'lar ve hatayı audit kayıtlarına yazar.
    """

    def form_valid(self, form):
        email = form.cleaned_data.get("email", "")
        backend_name = getattr(settings, "EMAIL_BACKEND", "?")
        try:
            response = super().form_valid(form)
            logger.info(
                "Password reset requested for %s (backend=%s, host=%s)",
                email, backend_name, getattr(settings, "EMAIL_HOST", "?"),
            )
            log_event(
                event_type="auth.password_reset_requested",
                actor=None,
                target_type="accounts.User",
                metadata={"email": email, "backend": backend_name},
                request=self.request,
            )
            return response
        except Exception as exc:
            logger.exception(
                "Password reset e-mail FAILED for %s (backend=%s): %s",
                email, backend_name, exc,
            )
            log_event(
                event_type="auth.password_reset_failed",
                actor=None,
                target_type="accounts.User",
                metadata={"email": email, "backend": backend_name, "error": str(exc)},
                request=self.request,
            )
            # Kullanıcıya generic mesaj ver; e-posta var/yok'un sızdırılmaması adına
            messages.error(
                self.request,
                _("E-posta gönderiminde bir sorun oluştu. Lütfen daha sonra tekrar deneyin veya yöneticinize başvurun."),
            )
            return redirect("accounts:password_reset")


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        request.session.set_expiry(0)
        log_auth_event(
            event_type="register",
            actor=user,
            request=request,
            description="Yeni hesap olusturuldu ve otomatik giris yapildi.",
        )
        messages.success(request, "Kayit basarili. Hos geldiniz.")
        return redirect("core:home")

    return render(request, "accounts/register.html", {"form": form})


@ensure_csrf_cookie
@login_throttle
@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    form = LoginForm(request=request, data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            clear_login_throttle(request, form.cleaned_data.get("login", ""))
            login(request, user)

            if form.cleaned_data.get("remember_me"):
                request.session.set_expiry(settings.SESSION_COOKIE_AGE)
            else:
                request.session.set_expiry(0)

            log_auth_event(
                event_type="login",
                actor=user,
                request=request,
                description="Kullanici giris yapti.",
            )
            messages.success(request, "Basariyla giris yaptiniz.")
            return redirect("core:home")
        if request.POST.get("login") and request.POST.get("password"):
            register_login_failure(request, request.POST.get("login", ""))

    return render(request, "accounts/login.html", {"form": form})


@require_POST
def logout_view(request):
    user = request.user if request.user.is_authenticated else None
    logout(request)
    log_auth_event(
        event_type="logout",
        actor=user,
        request=request,
        description="Kullanici cikis yapti.",
    )
    messages.info(request, "Cikis yapildi.")
    return redirect("core:home")


@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    """Kullanıcının kendi ad / soyad / e-postasını düzenleyebileceği profil sayfası."""
    user = request.user

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            log_event(
                event_type="user.profile_update",
                actor=user,
                target_type="accounts.User",
                target_id=str(user.pk),
                metadata={
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                request=request,
            )
            messages.success(request, _("Profil bilgileri güncellendi."))
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=user)

    # Extra read-only profile info depending on role
    profile_info = []
    if user.role == "student":
        try:
            sp = user.student_profile
            profile_info = [
                (_("Öğrenci no"), sp.student_no),
                (_("Bölüm"), str(sp.department) if sp.department else "—"),
                (_("Program"), str(sp.program) if sp.program else "—"),
                (_("Kayıt yılı"), str(sp.enrollment_year)),
                (_("Durum"), _("Onaylı") if sp.is_approved else _("Onay bekliyor")),
            ]
        except Exception:
            pass
    elif user.role == "instructor":
        try:
            ip = user.instructor_profile
            profile_info = [
                (_("Sicil no"), ip.employee_no),
                (_("Bölüm"), str(ip.department) if ip.department else "—"),
                (_("Unvan"), ip.title or "—"),
                (_("Durum"), _("Onaylı") if ip.is_approved else _("Onay bekliyor")),
            ]
        except Exception:
            pass

    ctx = {
        "form": form,
        "profile_info": profile_info,
        "pw_form": AkdPasswordChangeForm(user=user),
        "breadcrumb_items": items(
            home(),
            {"label": _("Profilim"), "url": None},
        ),
        "nav_namespace": "accounts",
        "nav_url_name": "profile",
    }
    return render(request, "accounts/profile.html", ctx)


@login_required
@require_http_methods(["GET", "POST"])
def password_change_view(request):
    """Şifre değiştirme; POST başarılıysa oturum korunur (update_session_auth_hash)."""
    if request.method == "POST":
        form = AkdPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            log_event(
                event_type="user.password_change",
                actor=request.user,
                target_type="accounts.User",
                target_id=str(request.user.pk),
                metadata={},
                request=request,
            )
            messages.success(request, _("Şifreniz başarıyla değiştirildi."))
            return redirect("accounts:profile")
        # Re-render profile page with the pw_form errors
        profile_form = ProfileForm(instance=request.user)
        profile_info = []
        u = request.user
        if u.role == "student":
            try:
                sp = u.student_profile
                profile_info = [
                    (_("Öğrenci no"), sp.student_no),
                    (_("Bölüm"), str(sp.department) if sp.department else "—"),
                    (_("Program"), str(sp.program) if sp.program else "—"),
                    (_("Kayıt yılı"), str(sp.enrollment_year)),
                    (_("Durum"), _("Onaylı") if sp.is_approved else _("Onay bekliyor")),
                ]
            except Exception:
                pass
        elif u.role == "instructor":
            try:
                ip = u.instructor_profile
                profile_info = [
                    (_("Sicil no"), ip.employee_no),
                    (_("Bölüm"), str(ip.department) if ip.department else "—"),
                    (_("Unvan"), ip.title or "—"),
                    (_("Durum"), _("Onaylı") if ip.is_approved else _("Onay bekliyor")),
                ]
            except Exception:
                pass
        ctx = {
            "form": profile_form,
            "profile_info": profile_info,
            "pw_form": form,
            "pw_error": True,
            "breadcrumb_items": items(
                home(),
                {"label": _("Profilim"), "url": None},
            ),
            "nav_namespace": "accounts",
            "nav_url_name": "profile",
        }
        return render(request, "accounts/profile.html", ctx)

    return redirect("accounts:profile")


@require_http_methods(["GET", "POST"])
def admin_request_view(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    if request.user.role == User.Role.ADMIN:
        messages.info(request, _("Zaten yönetici rolündesiniz."))
        return redirect("core:home")

    pending = AdminRequest.objects.filter(
        user=request.user,
        status=AdminRequest.Status.PENDING,
    ).first()

    if request.method == "POST":
        if pending:
            messages.warning(request, _("Zaten bekleyen bir talebiniz var."))
            return redirect("accounts:admin_request")
        form = AdminRequestForm(request.POST)
        if form.is_valid():
            ar = AdminRequest.objects.create(
                user=request.user,
                reason=(form.cleaned_data.get("reason") or "").strip(),
            )
            log_event(
                event_type="admin_request_created",
                actor=request.user,
                target_type="accounts.AdminRequest",
                target_id=str(ar.pk),
                metadata={"username": request.user.username},
                request=request,
            )
            messages.success(request, _("Talebiniz alındı. Kurucu yönetici inceleyecektir."))
            return redirect("accounts:admin_request")
    else:
        form = AdminRequestForm()

    history = AdminRequest.objects.filter(user=request.user).order_by("-created_at")[:20]
    return render(
        request,
        "accounts/admin_request.html",
        {
            "form": form,
            "pending_request": pending,
            "history": history,
        },
    )
