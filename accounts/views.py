from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST

from audit_logs.services import log_auth_event, log_event

from .forms import AdminRequestForm, LoginForm, RegisterForm
from .models import AdminRequest, User
from .login_throttle import clear_login_throttle, login_throttle, register_login_failure


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
