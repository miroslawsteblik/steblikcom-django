#!/usr/bin/env bash
set -e

python manage.py migrate --no-input
python manage.py collectstatic --no-input --clear
python manage.py shell -c "from django.conf import settings; from django.contrib.sites.models import Site; d=next(h for h in settings.ALLOWED_HOSTS if '.' in h); Site.objects.update_or_create(id=1, defaults={'domain':d,'name':d})"

exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 60 \
    --log-level info \
    --access-logfile -
