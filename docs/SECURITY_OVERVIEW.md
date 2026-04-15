# Güvenlik Özeti

Özet; ayrıntılı politika: `SECURITY.md`, tarama rehberi: `docs/security/code-scanning-and-secrets.md`.

## Kimlik ve yetkilendirme

| Kontrol | Uygulama |
|---------|-----------|
| Oturum | Django `contrib.auth`, güvenli parola hash |
| RBAC | `accounts.User.role` (admin / student / instructor); mixin’ler ve view kontrolleri (`core/permissions.py`) |
| Kurucu yönetici | `is_founder_admin`; yalnızca bu kullanıcı web üzerinden admin taleplerini onaylar |
| Django Admin | Staff/superuser; founder alan kısıtları (`accounts/admin.py`) |

## Web uygulaması sertleştirmesi

| Tehdit | Önlem |
|--------|--------|
| CSRF | `CsrfViewMiddleware`, formlarda `{% csrf_token %}` |
| SQLi | Django ORM / parametreli sorgular |
| XSS | Şablon otomatik kaçışı açık |
| Clickjacking | `XFrameOptionsMiddleware` |
| Brute-force (giriş) | `LoginBruteForceMiddleware` |
| Hız sınırlama | Enrollment POST için `django-ratelimit` (özellik bayrakları: `RATELIMIT_ENABLE`, `FEATURE_ENROLLMENT_RATELIMIT`) |

## Üretim ayarları

`config/settings/prod.py`: `DEBUG=False`, TLS yönlendirme ve HSTS (proxy arkasında), güvenli çerezler, `CSRF_TRUSTED_ORIGINS`, `SECRET_KEY` zorunluluğu.

## Loglama ve sızdırma riski

- `core/logging_utils.RedactingFormatter` — yaygın gizli desen maskeleme.
- JSON log modunda structlog ile ek alanlar; `request_id` korelasyonu (`docs/observability.md`).

## Denetim (audit)

- `audit_logs` uygulaması; kritik işlemler için olay kaydı (ör. admin talebi kararı).

## CI / bağımlılık

| Araç | Rol |
|------|-----|
| `pip-audit --strict` | Bilinen CVE’li pin’leri bloklar |
| Bandit | Statik kod güvenliği; SARIF yükleme (CI) |
| detect-secrets | `.secrets.baseline` ile sızıntı taraması (Phase 9 kapısı) |
| Dependabot | `.github/dependabot.yml` |

## Operasyonel kontrol listesi (kısa)

- [ ] `.env` repoda yok; üretim sırları yalnızca ortam / secret store.
- [ ] `main` için branch protection ve zorunlu CI job’ları.
- [ ] RDS güvenlik grubu sıkı; S3 bucket IAM ve public erişim politikası gözden geçirildi.
