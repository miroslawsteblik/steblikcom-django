#!/usr/bin/env bash
set -e

python manage.py migrate --no-input
python manage.py collectstatic --no-input --clear

exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 60 \
    --log-level info \
    --access-logfile -
