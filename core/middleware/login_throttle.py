"""
Giriş brute-force koruması middleware'i — başarısız denemelerde IP/kullanıcı bazlı blokaj.
"""
from django.contrib import messages
from django.shortcuts import redirect

from accounts.services.login_throttle import is_login_locked


class LoginBruteForceMiddleware:
    """POST /accounts/login/ isteklerinde IP+kullanici kilidini kontrol eder."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path.rstrip("/")
        if request.method == "POST" and path.endswith("/accounts/login"):
            raw = request.POST.get("login", "")
            if is_login_locked(request, raw):
                messages.error(
                    request,
                    "Cok fazla basarisiz giris denemesi. Lutfen daha sonra tekrar deneyin.",
                )
                return redirect("accounts:login")
        return self.get_response(request)
