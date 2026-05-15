"""ParkiPay — Django Admin: Billing"""
from django.contrib import admin
from apps.billing.models import ControlNumber


@admin.register(ControlNumber)
class ControlNumberAdmin(admin.ModelAdmin):
    list_display = [
        "control_number", "plate_number", "officer", "location",
        "amount_due", "status", "generated_at", "expires_at", "sms_sent",
    ]
    list_filter = ["status", "sms_sent", "location"]
    search_fields = ["control_number", "plate_number", "officer__employee_id"]
    readonly_fields = ["control_number", "generated_at", "created_at"]
    ordering = ["-generated_at"]
