"""
ParkiPay — Celery Application
Handles async tasks: SMS dispatch, email dispatch, control number expiry sweep.
"""

import os

from celery import Celery

env = os.environ.get("DJANGO_ENV", "local")
settings_map = {
    "local": "core.settings.local",
    "staging": "core.settings.production",
    "production": "core.settings.production",
}
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_map.get(env, "core.settings.local"))

app = Celery("parkipay")

# Read broker/backend config from Django settings (CELERY_* keys)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Sanity-check task — run with: celery -A core call core.celery.debug_task"""
    print(f"Request: {self.request!r}")


# ── Periodic tasks (Sprint 4+) ─────────────────────────────────────────────────
# app.conf.beat_schedule = {
#     "expire-control-numbers-every-minute": {
#         "task": "apps.billing.tasks.expire_stale_control_numbers",
#         "schedule": 60.0,
#     },
# }
