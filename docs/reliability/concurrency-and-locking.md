# Concurrency and locking (enrollment capacity)

## Problem

Iki ogrenci ayni anda son kontenjan koltuguna kayit olmaya calisirsa, klasik “count sonra insert” yarisi ile gecici **oversubscription** olusabilir.

## Cozum

`core/services/enrollment_atomic.py`:

- `transaction.atomic()` icinde `CourseSection.objects.select_for_update(of=("self",))` ile satir kilidi.
- Ardindan `Enrollment.save()` → `validate_capacity` mevcut sayimi gorur.

## Idempotency

- DB: `uniq_enrollment_student_section` (mevcut) — ayni ogrenci+section tekrar insert **IntegrityError**.
- Uygulama: `IntegrityError` kullaniciya anlasilir mesaj ile dondurulur.

## Rate limit

- `StudentEnrollView` POST: `django-ratelimit` (varsayilan 60/dk / kullanici).
- `FEATURE_ENROLLMENT_RATELIMIT=False` veya `RATELIMIT_ENABLE=False` ile kapatilabilir (test/ozel durum).

## Testler

- `core/test_phase8_concurrency.py`: MySQL’de iki thread son koltuk — yalnizca biri basarili.
- Yerel SQLite: sinif `@skipUnless(connection.vendor == "mysql")` ile atlanir; CI MySQL ile calisir.

## SQLite / gelistirme

SQLite’da `select_for_update` sinirli semantik; kapasite yarisi testi CI’da dogrulanir.
