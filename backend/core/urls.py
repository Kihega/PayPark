"""ParkiPay — Root URL Configuration"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.utils import timezone


def health_check(request):
    """
    GET /api/health/
    Lightweight endpoint used by Render health checks, monitoring, and CI/CD
    pipeline verification. Returns 200 as long as Django is running.
    """
    return JsonResponse(
        {
            "status": "ok",
            "service": "ParkiPay API",
            "version": "1.0.0",
            "timestamp": timezone.now().isoformat(),
            "environment": (
                "production"
                if not __import__("django").conf.settings.DEBUG
                else "development"
            ),
        },
        status=200,
    )


urlpatterns = [
    # ── Admin ──────────────────────────────────────────────────────────────
    path("admin/", admin.site.urls),
    # ── Health check ───────────────────────────────────────────────────────
    path("api/health/", health_check, name="health-check"),
    # ── Auth ──────────────────────────────────────────────────────────────
    path("api/auth/", include("apps.accounts.urls")),
    # ── Vehicles ──────────────────────────────────────────────────────────
    path("api/vehicles/", include("apps.vehicles.urls")),
    # ── Billing ───────────────────────────────────────────────────────────
    path("api/billing/", include("apps.billing.urls")),
]
