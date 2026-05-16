"""ParkiPay — WSGI entry point for Gunicorn / Render."""

import os

from django.core.wsgi import get_wsgi_application

env = os.environ.get("DJANGO_ENV", "local")
settings_map = {
    "local": "core.settings.local",
    "staging": "core.settings.production",
    "production": "core.settings.production",
}
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_map.get(env, "core.settings.local"))

application = get_wsgi_application()
