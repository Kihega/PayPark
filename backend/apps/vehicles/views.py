"""ParkiPay — Vehicles Views (Sprint 2)"""

# Sprint 2 implementation:
#   GET /api/vehicles/lookup/?plate=TZ001ABC
#   GET /api/vehicles/locations/
from django.http import JsonResponse


def placeholder(request):
    return JsonResponse(
        {"detail": "Sprint 2 — Vehicle lookup coming soon."}, status=501
    )
