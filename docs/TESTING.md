# Test Stratejisi

## Test türleri

| Tür | Araç / konum | Amaç |
|-----|----------------|------|
| Django birim/entegrasyon | `python manage.py test`, `core/test_phase4.py`, `core/test_phase6.py`, `core/test_phase8_concurrency.py` | İş kuralları (kayıt, önkoşul, GPA, RBAC, HTTP kenarları) |
| Pytest işaretli | `tests/`, `pytest.ini` / `pyproject` marker’ları (`unit`, `integration`, `smoke`, `concurrency`, `security`) | Phase 9 CI kapıları ile hizalı paket |
| Eşzamanlılık | `tests/enrollments/test_enrollment_concurrency.py`, `core/test_phase8_concurrency.py` | MySQL altında satır kilidi ve yarış senaryoları |
| Kurucu / admin talebi | `tests/test_admin_request.py` | Founder onayı ve yetki sınırları |

## Komutlar

### Günlük geliştirme

```bash
set DJANGO_SETTINGS_MODULE=config.settings.dev
python manage.py test
```

PowerShell (tek oturum):

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.dev"
python manage.py test
```

### Coverage (CI ile uyumlu eşik)

`pyproject.toml` → `[tool.coverage.report]` **`fail_under = 75`** ( `coverage run manage.py test` sonrası `coverage report`).

```bash
coverage erase
coverage run manage.py test
coverage report
coverage html
```

### Makefile (bash ortamı)

| Hedef | İçerik |
|-------|--------|
| `make test` | Tüm pytest marker birleşimi |
| `make test-unit` | `-m unit` |
| `make ci` | Güvenlik taraması + migration smoke + pytest + **%80** coverage eşiği (`--cov-fail-under=80`) |

Phase 9 iş akışı: `.github/workflows/phase9-ci.yml` (pytest marker’lar, migration smoke, detect-secrets).

### CI (GitHub Actions)

- Ana pipeline: `.github/workflows/ci.yml` — Ruff, pip-audit, Bandit, MySQL üzerinde `manage.py test` + Codecov + SBOM.
- Ek: `phase9-ci.yml` daha sıkı kapılar için.

## Coverage beklentisi

- **Minimum (repo standardı)**: satır coverage **≥ %75** (`manage.py test` + coverage raporu).
- **Phase 9 `make ci`**: **≥ %80** (yayın öncesi tam kapı).
- Yeni kod: mümkün olduğunca kritik servis ve view yollarını test ile kapatın; yalnızca migration dosyaları hariç tutulur (`pyproject.toml` `omit`).

## Test verisi

- Opsiyonel fixture: `python manage.py loaddata phase4_seed` — şifreler `AGENTS.md` / README.
- Kurucu atama: `python manage.py set_founder_admin <kullanici_adi>`.

## Sorun giderme

| Sorun | Çözüm |
|-------|--------|
| MySQL bağlantı hatası | `DATABASE_URL` veya `DB_*`, `cryptography` kurulu mu |
| CI’da migration | `config.settings.ci` ve boş test veritabanı |
| pytest bulunamadı | `pip install -r requirements-dev.txt` |
