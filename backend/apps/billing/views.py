"""ParkiPay — Billing Views (Sprint 3)"""
# Sprint 3 implementation:
#   POST /api/billing/generate/       — global duplicate check + generate
#   GET  /api/billing/history/        — officer daily bill history
#   GET  /api/billing/<cn>/status/    — SMS/email delivery status
from django.http import JsonResponse


def placeholder(request):
    return JsonResponse({"detail": "Sprint 3 — Billing coming soon."}, status=501)
