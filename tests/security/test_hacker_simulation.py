"""
Hacker simülasyonu — kötü niyetli bir kullanıcı senaryosu.

Bu modül "blue team" perspektifinden saldırgan davranışlarını canlandırır
ve sistemin OWASP Top 10 sınıflarına karşı dayanıklı olduğunu doğrular:
- A01 Broken Access Control: anonim & yatay/dikey yetki yükseltme, IDOR
- A03 Injection: SQL injection, template injection, XSS payload reflect
- A05 Security Misconfiguration: CSRF zorunluluğu, clickjacking, security headers
- A07 Identification/Auth Failures: brute force, weak password
- A10 SSRF/Open Redirect: redirect parametresi kötüye kullanımı
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

pytestmark = [pytest.mark.security, pytest.mark.django_db]

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures: saldırgan ve kurban hesaplar
# ---------------------------------------------------------------------------


@pytest.fixture
def attacker():
    """Saldırgan: standart bir öğrenci hesabı."""
    return User.objects.create_user(
        username="mr_hacker",
        email="hacker@evil.test",
        password="h4ck-th3-pl4n3t-2026",
        role=User.Role.STUDENT,
    )


@pytest.fixture
def victim_student():
    return User.objects.create_user(
        username="ayse_yilmaz",
        email="ayse@uni.test",
        password="V1ctimSecret-9090",
        role=User.Role.STUDENT,
    )


@pytest.fixture
def real_admin():
    return User.objects.create_user(
        username="root_admin",
        email="root@uni.test",
        password="Adm1n-Pass-Long-2026",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def attacker_client(attacker, client):
    client.force_login(attacker)
    return client


# ---------------------------------------------------------------------------
# 1) A01 — Anonim erişim: korumalı sayfalar login'e yönlendirmeli
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "urlname",
    [
        "dashboard:index",
        "students:index",
        "students:transcript",
        "instructors:index",
        "academic:announcement_list",
        "academic:department_list",
        "courses:course_list",
        "courses:offering_list",
        "enrollments:browse",
        "audit_logs:index",
        "accounts:admin_request",
    ],
)
def test_anonymous_user_cannot_reach_protected_pages(client, urlname):
    """Anonim ziyaretçi kimlik gerektiren sayfaları çekemez."""
    url = reverse(urlname)
    response = client.get(url)
    # 302 (login redirect) ya da 403 kabul edilebilir.
    assert response.status_code in (302, 403), (
        f"{urlname} anonim erişime açık görünüyor (status={response.status_code})."
    )
    if response.status_code == 302:
        assert "/accounts/login" in response.url or "login" in response.url.lower()


# ---------------------------------------------------------------------------
# 2) A01 — Yetki yükseltme: öğrenci admin sayfalarına giremez
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "urlname",
    [
        "academic:department_create",
        "academic:announcement_create",
        "courses:course_create",
        "courses:offering_create",
        "dashboard:admin_requests",
        "audit_logs:index",
    ],
)
def test_student_cannot_access_admin_only_pages(attacker_client, urlname):
    """Öğrenci rolüyle yönetici sayfaları açılırsa 403/302 dönmeli."""
    url = reverse(urlname)
    response = attacker_client.get(url)
    assert response.status_code in (302, 403, 404), (
        f"{urlname} öğrenciye 200 döndürdü — privilege escalation riski."
    )


# ---------------------------------------------------------------------------
# 3) A01 — IDOR: saldırgan başka kullanıcının admin talebini onaylayamaz
# ---------------------------------------------------------------------------


def test_idor_admin_request_approve_blocked_for_student(attacker_client, victim_student):
    """
    Saldırgan kendi student session'ında /dashboard/admin-talepleri/<id>/approve/
    URL'ini doğrudan çağırarak yetki yükseltme deneyemez.
    """
    from accounts.models import AdminRequest

    req = AdminRequest.objects.create(user=victim_student, reason="legit")
    url = reverse("dashboard:admin_request_approve", args=[req.pk])
    response = attacker_client.post(url, follow=False)

    assert response.status_code in (302, 403, 404)
    req.refresh_from_db()
    assert req.status == AdminRequest.Status.PENDING, (
        "Öğrenci IDOR ile admin talebini onaylayabildi — kritik privilege escalation."
    )


# ---------------------------------------------------------------------------
# 4) A03 — SQL Injection: katalog/duyuru aramasında payload nötralize edilir
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        "' OR '1'='1",
        "'; DROP TABLE accounts_user; --",
        '" OR 1=1 --',
        "1) UNION SELECT password FROM accounts_user --",
    ],
)
def test_sql_injection_payloads_are_safely_handled(attacker_client, payload):
    """ORM parametreli sorgu kullandığından arama bu payload'larda 200/302 dönmeli, 500 değil."""
    url = reverse("courses:course_list")
    response = attacker_client.get(url, {"q": payload, "search": payload})
    assert response.status_code in (200, 302), (
        f"SQLi payload ({payload!r}) 500 üretti — ham SQL kullanılıyor olabilir."
    )
    # Şifre veya hash kelimesinin gövdeye dökülmediğini doğrula
    body = response.content.decode("utf-8", errors="ignore").lower()
    assert "pbkdf2" not in body and "md5$" not in body, "Şifre hash'i sızıyor."


# ---------------------------------------------------------------------------
# 5) A03 — Reflected XSS: kullanıcı girdisi escape edilir
# ---------------------------------------------------------------------------


def test_xss_payload_is_escaped_in_login_form(client):
    """Login form, GET üzerinden gelen ?next=<script> gibi payload'ı yansıtırsa escape etmeli."""
    payload = '<script>alert("xss-from-hacker")</script>'
    url = reverse("accounts:login")
    response = client.get(url, {"next": payload})
    assert response.status_code == 200
    body = response.content.decode("utf-8")
    # Çiğ <script> etiketi sayfaya dökülmemeli; Django auto-escape devrede olmalı.
    assert "<script>alert(\"xss-from-hacker\")</script>" not in body, (
        "Reflected XSS: payload escape edilmeden DOM'a yazılıyor."
    )


def test_xss_payload_in_register_form_is_escaped(client):
    """Register POST'una atılan script payload'ı hata sayfasında ham olarak gözükmemeli."""
    payload = '"><svg/onload=alert(1)>'
    url = reverse("accounts:register")
    response = client.post(
        url,
        data={
            "username": payload,
            "email": "x@x.test",
            "password1": "ShortPass1!",
            "password2": "different",
            "role": "student",
        },
    )
    body = response.content.decode("utf-8", errors="ignore")
    assert "<svg/onload=alert(1)>" not in body, "Form hatasında XSS payload escape edilmiyor."


# ---------------------------------------------------------------------------
# 6) A05 — CSRF: token olmadan POST reddedilir
# ---------------------------------------------------------------------------


def test_csrf_required_for_logout_post(attacker, settings):
    """
    enforce_csrf_checks=True ile çalışan istemci, token vermeden logout'u zorlayamamalı.
    Bu, başka sitelerden gelen otomatik POST'ların engellendiğini garanti eder.
    """
    settings.DEBUG = False  # 403 sayfasına düşmesi için
    raw = Client(enforce_csrf_checks=True)
    raw.force_login(attacker)
    response = raw.post(reverse("accounts:logout"))
    assert response.status_code == 403, (
        "CSRF koruması logout endpoint'inde devre dışı — CSRF token zorunlu olmalı."
    )


def test_csrf_required_for_admin_request_post(attacker):
    """Admin talebi oluşturma POST'u CSRF token olmadan kabul edilmemeli."""
    raw = Client(enforce_csrf_checks=True)
    raw.force_login(attacker)
    response = raw.post(reverse("accounts:admin_request"), data={"reason": "I want it"})
    assert response.status_code == 403, "Admin request POST'unda CSRF koruması yok."


# ---------------------------------------------------------------------------
# 7) A05 — Clickjacking & header tabanlı saldırı yüzeyi
# ---------------------------------------------------------------------------


def test_clickjacking_protection_via_x_frame_options(client):
    """Login sayfası iframe'e gömülemez (UI redress saldırılarına karşı)."""
    response = client.get(reverse("accounts:login"))
    assert response.status_code == 200
    assert response.headers.get("X-Frame-Options", "").upper() in {"DENY", "SAMEORIGIN"}, (
        "X-Frame-Options yok veya yanlış; clickjacking riski."
    )


def test_content_type_options_nosniff_present(client):
    response = client.get(reverse("accounts:login"))
    assert response.headers.get("X-Content-Type-Options", "").lower() == "nosniff"


def test_csp_header_present_on_protected_page(attacker_client):
    """Authenticated bir sayfada CSP header'ı bulunmalı."""
    response = attacker_client.get(reverse("core:home"))
    assert "Content-Security-Policy" in response.headers, "CSP header eksik."


# ---------------------------------------------------------------------------
# 8) A07 — Zayıf parola reddedilir
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "weak",
    [
        "12345678",         # NumericPasswordValidator
        "password",         # CommonPasswordValidator
        "qwerty",           # CommonPassword + MinimumLength
        "abc",              # MinimumLength
    ],
)
def test_weak_passwords_are_rejected_on_register(client, weak):
    response = client.post(
        reverse("accounts:register"),
        data={
            "username": f"weak_{abs(hash(weak)) % 9999}",
            "email": f"weak_{abs(hash(weak)) % 9999}@uni.test",
            "password1": weak,
            "password2": weak,
            "role": "student",
        },
    )
    # Başarılı kayıt 302, başarısızlık 200 (form tekrar render)
    assert response.status_code == 200, (
        f"Zayıf parola '{weak}' kaydı geçti — parola politikası uygulanmıyor."
    )
    assert not User.objects.filter(username__startswith="weak_").exists() or (
        not User.objects.filter(username__startswith="weak_").first().check_password(weak)
    ), "Zayıf parola DB'ye yazıldı."


# ---------------------------------------------------------------------------
# 9) A07 — Kullanıcı sayım: var olmayan vs yanlış parola aynı yanıtı vermeli
# ---------------------------------------------------------------------------


def test_login_does_not_leak_user_existence(client, victim_student):
    """
    'Bu kullanıcı yok' vs 'parola yanlış' farklı mesajlarla dönerse saldırgan
    geçerli kullanıcı adlarını sayabilir. Yanıt status'u ve genel form hatası aynı olmalı.
    """
    nonexistent = client.post(
        reverse("accounts:login"),
        data={"login": "ghost_user_does_not_exist", "password": "anything"},
    )
    wrongpass = client.post(
        reverse("accounts:login"),
        data={"login": "ayse_yilmaz", "password": "definitely-wrong-1234"},
    )
    assert nonexistent.status_code == wrongpass.status_code, (
        "Var olmayan kullanıcı ile yanlış parola farklı status üretiyor — kullanıcı sayım riski."
    )


# ---------------------------------------------------------------------------
# 10) A10 — Open redirect: ?next= manipülasyonu engellenir
# ---------------------------------------------------------------------------


def test_login_open_redirect_to_external_host_blocked(client, victim_student):
    """Login sonrası ?next=http://evil.test gibi harici hedefe yönlenmemeli."""
    response = client.post(
        reverse("accounts:login") + "?next=http://evil.test/steal",
        data={"login": "ayse_yilmaz", "password": "V1ctimSecret-9090"},
        follow=False,
    )
    if response.status_code == 302:
        location = response["Location"]
        assert "evil.test" not in location, (
            f"Open redirect riski: login post → {location}"
        )


# ---------------------------------------------------------------------------
# 11) A07 — Session fixation: login sonrası session anahtarı değişmeli
# ---------------------------------------------------------------------------


def test_session_key_rotates_on_login(client, victim_student):
    """Django default davranışı: login sonrası session anahtarı değişir."""
    pre = client.session.session_key  # boş olabilir
    client.post(
        reverse("accounts:login"),
        data={"login": "ayse_yilmaz", "password": "V1ctimSecret-9090"},
    )
    post = client.session.session_key
    assert post is not None
    assert pre != post, "Login session fixation: anahtar dönmüyor."


# ---------------------------------------------------------------------------
# 12) Cookie güvenliği: session/CSRF cookie HttpOnly olmalı
# ---------------------------------------------------------------------------


def test_session_cookie_has_httponly_flag(client, victim_student):
    client.post(
        reverse("accounts:login"),
        data={"login": "ayse_yilmaz", "password": "V1ctimSecret-9090"},
    )
    session_cookie = client.cookies.get("sessionid")
    assert session_cookie is not None, "Login sonrası session cookie set edilmedi."
    assert session_cookie["httponly"], "sessionid cookie HttpOnly değil — JS ile çalınabilir."


# ---------------------------------------------------------------------------
# 13) Admin URL gizli mi: /admin/ panel anonime kapalı
# ---------------------------------------------------------------------------


def test_django_admin_requires_authentication(client):
    response = client.get("/admin/", follow=False)
    assert response.status_code in (302, 403), "Django admin anonim erişime açık görünüyor."
