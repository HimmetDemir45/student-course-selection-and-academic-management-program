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

# Kapsamlı ders/müfredat/eğitimci seed — SEED_COMPREHENSIVE=1 ise çalışır (idempotent).
if [ "${SEED_COMPREHENSIVE:-0}" = "1" ]; then
    python manage.py seed_comprehensive
fi

# CourseOffering + CourseSection + SectionTimeSlot seed — SEED_REAL_DATA=1 ise çalışır.
if [ "${SEED_REAL_DATA:-0}" = "1" ]; then
    python manage.py seed_real_data
fi

# Öğrenci profili + transkript seed — SEED_STUDENTS=1 ise çalışır.
# Yunus ve Gürkan mevcut kullanıcı; kullanıcı adları farklıysa YUNUS_USERNAME ve GURKAN_USERNAME ayarlayın.
if [ "${SEED_STUDENTS:-0}" = "1" ]; then
    EXTRA_ARGS=""
    if [ -n "$YUNUS_USERNAME" ]; then
        EXTRA_ARGS="$EXTRA_ARGS --yunus-username=$YUNUS_USERNAME"
    fi
    if [ -n "$GURKAN_USERNAME" ]; then
        EXTRA_ARGS="$EXTRA_ARGS --gurkan-username=$GURKAN_USERNAME"
    fi
    python manage.py seed_students_transcripts $EXTRA_ARGS
fi

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile -
