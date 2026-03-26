#!/usr/bin/env bash
set -euo pipefail

echo "[migration-smoke] Basladi"

if [[ ! -f "manage.py" ]]; then
  echo "[migration-smoke] HATA: manage.py bulunamadi."
  exit 1
fi

echo "[migration-smoke] Django check"
python manage.py check

echo "[migration-smoke] Tum migrationlari uygula"
python manage.py migrate --noinput

APP="${MIGRATION_APP:-enrollments}"
echo "[migration-smoke] Test app: ${APP}"

MIGRATIONS=$(
  python manage.py showmigrations "${APP}" --list \
    | awk '/^\s*\[.\]\s+[0-9][0-9][0-9][0-9]_/ {print $2}'
)

if [[ -z "${MIGRATIONS}" ]]; then
  echo "[migration-smoke] HATA: ${APP} icin migration bulunamadi."
  exit 1
fi

LAST_MIGRATION=$(echo "${MIGRATIONS}" | tail -n 1)
PREV_MIGRATION=$(echo "${MIGRATIONS}" | tail -n 2 | head -n 1)

echo "[migration-smoke] Son migration: ${LAST_MIGRATION}"
if [[ -n "${PREV_MIGRATION}" && "${PREV_MIGRATION}" != "${LAST_MIGRATION}" ]]; then
  echo "[migration-smoke] Rollback: ${APP} -> ${PREV_MIGRATION}"
  python manage.py migrate "${APP}" "${PREV_MIGRATION}" --noinput
else
  echo "[migration-smoke] Tek migration tespit edildi, rollback ${APP} -> zero"
  python manage.py migrate "${APP}" zero --noinput
fi

echo "[migration-smoke] Yeniden apply: ${APP} -> ${LAST_MIGRATION}"
python manage.py migrate "${APP}" "${LAST_MIGRATION}" --noinput

echo "[migration-smoke] Son durum dogrulama"
python manage.py migrate --noinput

echo "[migration-smoke] BASARILI"
