# Code scanning, SARIF, SBOM, secrets

## Codecov

- CI: `codecov/codecov-action` `coverage.xml` yukler.
- Ozel repo: **Repository secret** `CODECOV_TOKEN` (Codecov.io).
- PR’larda coverage diff icin Codecov GitHub App kurulumu onerilir.

## SARIF (Bandit)

- CI `security` job: `bandit -c .bandit -r . -f sarif -o bandit.sarif --exit-zero`
- `github/codeql-action/upload-sarif` → **Security** sekmesi (Code scanning alerts).
- Fork PR’larda upload izin kisiti olabilir; `continue-on-error: true`.

## Sonuclari okuma

- **Codecov**: PR yorumu / checks; dusen coverage kritik path’leri isaret eder.
- **Code scanning**: Bandit bulgulari severity ile; false positive’leri “dismiss” + kural disi `.bandit` ile yonetin.

## SBOM (CycloneDX)

- Artifact: `sbom-cyclonedx` (workflow run).
- Komut: `python -m cyclonedx_py requirements requirements.txt -o sbom.json`
- Tedarik zinciri denetimi ve lisans envanteri icin saklayin.

## Secrets hygiene

- `pip-audit --strict` bagimlilik CVE.
- GitHub: Secret scanning + push protection.
- **Asla** token’i SARIF/log/coverage ciktisina yazmayin.

## CORS ve guvenlik basliklari (final audit ozeti)

- Uygulama **sunucu tarafli HTML** odakli; tarayicidan baska origin’e API acilmiyorsa **django-cors-headers** zorunlu degil.
- Prod: `SECURE_SSL_REDIRECT`, HSTS, `X_FRAME_OPTIONS=DENY`, `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_REFERRER_POLICY`, guvenli cerezler (`config/settings/prod.py`).
- Ileride SPA + API ayri subdomain ise: `django-cors-headers` ile whitelist origin; **never** `CORS_ALLOW_ALL_ORIGINS=True` prod’da.

## Rate limit ozeti

- Login: mevcut brute-force middleware + oturum kilidi.
- Enrollment POST: `django-ratelimit` (ayar: `FEATURE_ENROLLMENT_RATELIMIT`, `RATELIMIT_ENABLE`).
