#!/bin/sh
set -e

: "${DJANGO_SETTINGS_MODULE:=config.settings.render}"

python manage.py migrate --noinput
python manage.py collectstatic --noinput --ignore tailwind-input.css

# Kurucu yönetici bootstrap — yalnızca FOUNDER_ADMIN_EMAIL ayarlıysa çalışır.
# Hesap oluştuktan sonra env var'ı kaldırmak isteğe bağlıdır (idempotent).
if [ -n "$FOUNDER_ADMIN_EMAIL" ]; then
    python manage.py bootstrap_founder_admin
fi

# Demo veri seed — yalnızca SEED_DEMO_DATA=1 ise çalışır (idempotent).
if [ "${SEED_DEMO_DATA:-0}" = "1" ]; then
    python manage.py seed_demo_users
fi

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile -
