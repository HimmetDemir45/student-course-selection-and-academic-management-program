from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from audit_logs.services import log_auth_event

from .forms import LoginForm, RegisterForm


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


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    form = LoginForm(request=request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
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
