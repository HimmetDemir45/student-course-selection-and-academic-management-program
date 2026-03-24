# Backup restore dry-run checklist

Uretim veritabanini dogrudan dokunmadan prosedur dogrulama.

## Amaç

RDS snapshot veya logical dump ile **staging** ortamına geri yükleme adımlarının tekrarlanabilir olduğunu kanıtlamak.

## Dry-run adımları (çeyrek dönem)

1. Son otomatik snapshot ID’sini not edin.
2. Boş veya staging RDS instance oluşturun; snapshot’tan restore (farklı endpoint).
3. Staging `.env` içinde `DATABASE_URL`’i yeni instance’a yönlendirin.
4. `python manage.py migrate --plan` (beklenen: “no changes” veya bilinen fark).
5. Salt okunur sorgular: `students_studentprofile`, `enrollments_enrollment` kayıt sayıları üretimle kaba karşılaştırma (PII maskeleme).
6. Uygulama smoke: staging URL ile `/health/ready/`.
7. Sonucu tarih + sahip ile wiki/ticket’a yazın.

## Otomasyon (gelecek)

AWS CLI ile snapshot list + restore script’i pipeline’a eklenmesi (Phase 9); şimdilik manuel tetik yeterli.
