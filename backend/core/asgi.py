"""ParkiPay — ASGI entry point (future WebSocket / async support)."""
import os

from django.core.asgi import get_asgi_application

env = os.environ.get("DJANGO_ENV", "local")
settings_map = {
    "local": "core.settings.local",
    "staging": "core.settings.production",
    "production": "core.settings.production",
}
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      settings_map.get(env, "core.settings.local"))

application = get_asgi_application()
