# PHASE 9 RUNBOOK

## CI Fail Karar Agaci
- Test fail:
  - `make test` ile lokal tekrar et.
  - Hata yalniz concurrency/security ise issue ac, release blokla.
- Security scan fail:
  - `make security-scan` calistir.
  - Critical/High kapatmadan merge/deploy yapma.
- Migration smoke fail:
  - `make migration-smoke` tekrar et.
  - Rollback testi gecmeden release durdur.
- Coverage fail:
  - Global `<80` veya kritik modul `<90` ise release durdur.

## Release Oncesi Checklist
- [ ] `make ci` gecti
- [ ] Security scan temiz
- [ ] Migration smoke + rollback smoke gecti
- [ ] Health endpoint erisilebilir
- [ ] Synthetic canary degiskenleri dolu (`CANARY_*`)
- [ ] Rollback etiketi (`PREVIOUS_STABLE_TAG`) hazir

## Canary Fail Rollback Proseduru
- Canary job fail ise:
  - `./scripts/rollback_release.sh --image <image_repo> --tag <stable_tag>`
- Dry-run dogrulama:
  - `./scripts/rollback_release.sh --image <image_repo> --tag <stable_tag> --dry-run`
- Rollback sonrasi:
  - Health check + canary tekrar calistir
  - Incident kaydi ac

## Migration Fail Rollback Proseduru
- Uygulama:
  - `python manage.py migrate --noinput` fail ise migration adini not et
- Geri donus:
  - `python manage.py migrate <app> <prev_migration> --noinput`
- Sonrasi:
  - `python manage.py migrate --plan`
  - Veri butunlugu kritik sorgularini calistir

## Secret Rotation Mini Proseduru
- Her 90 gunde bir:
  - Secret yeni versiyon olustur
  - Uygulamayi yeni secret ile deploy et
  - Health + canary dogrula
  - Eski versiyonu devre disi birak
- Acil sizinti:
  - Aninda revoke + rotate + incident tetikle

## DR Mini Tatbikat Adimlari
- [ ] Son backup ile restore denemesi
- [ ] Uygulama ayaga kalkis dogrulamasi
- [ ] Login + enrollment smoke
- [ ] RTO/RPO olcumu kayit altina al
- [ ] Tatbikat sonrasi iyilestirme maddeleri ac
