"""ParkiPay — Django Admin: Accounts"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.accounts.models import AuditLog, Officer


@admin.register(Officer)
class OfficerAdmin(UserAdmin):
    model = Officer
    list_display = ["employee_id", "full_name", "role", "location", "is_active", "created_at"]
    list_filter = ["role", "is_active", "location"]
    search_fields = ["employee_id", "full_name", "email", "phone"]
    ordering = ["full_name"]

    fieldsets = (
        (None, {"fields": ("employee_id", "password")}),
        ("Personal Info", {"fields": ("full_name", "phone", "email")}),
        ("Role & Location", {"fields": ("role", "location")}),
        ("Status", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Lockout", {"fields": ("failed_login_attempts", "locked_until")}),
        ("Timestamps", {"fields": ("created_at", "updated_at", "last_login")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("employee_id", "full_name", "role", "location", "password1", "password2"),
            },
        ),
    )
    readonly_fields = ["created_at", "updated_at", "last_login", "failed_login_attempts", "locked_until"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "officer", "action", "plate_number", "control_number", "result", "ip_address"]
    list_filter = ["action", "result"]
    search_fields = ["officer__employee_id", "plate_number", "control_number", "ip_address"]
    readonly_fields = [f.name for f in AuditLog._meta.fields]
    ordering = ["-timestamp"]

    def has_add_permission(self, request):
        return False  # Audit log is immutable

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
