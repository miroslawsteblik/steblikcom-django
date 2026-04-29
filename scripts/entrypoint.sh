#!/usr/bin/env bash
set -euo pipefail

# Run migrations on startup. Idempotent. Safe for single-instance deployments.
# If you ever scale to multiple replicas, move this to a one-shot job.
python apps/web/manage.py migrate --noinput

exec "$@"
