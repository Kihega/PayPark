#!/bin/bash
# ParkiPay — Docker Entrypoint
set -e

echo "==> Running database migrations..."
python manage.py migrate --noinput

echo "==> Starting Gunicorn..."
exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --worker-class sync \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
