"""ParkiPay — Auth Serializers"""
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from apps.accounts.models import Officer, AuditLog, log_action


# ── Officer Profile Serializer ────────────────────────────────────────────────

class OfficerProfileSerializer(serializers.ModelSerializer):
    location_name = serializers.SerializerMethodField()

    class Meta:
        model = Officer
        fields = [
            "id",
            "employee_id",
            "full_name",
            "phone",
            "email",
            "role",
            "location_name",
            "is_active",
            "created_at",
            "last_login",
        ]
        read_only_fields = fields

    def get_location_name(self, obj):
        return str(obj.location) if obj.location else None


# ── Custom JWT Token Serializer ───────────────────────────────────────────────

class ParkiPayTokenObtainSerializer(TokenObtainPairSerializer):
    """
    Extends the default JWT serializer to:
    1. Accept employee_id (not username)
    2. Enforce account lockout (5 failed attempts)
    3. Write every attempt to the audit log
    4. Embed role in the token payload
    """
    username_field = "employee_id"

    def validate(self, attrs):
        employee_id = attrs.get("employee_id", "")
        password = attrs.get("password", "")

        # ── Look up the officer ────────────────────────────────────────────
        try:
            officer = Officer.objects.get(employee_id=employee_id)
        except Officer.DoesNotExist:
            # Log failure without revealing whether account exists
            log_action(
                None,
                AuditLog.Action.LOGIN_FAILURE,
                result="account_not_found",
                extra={"employee_id": employee_id},
            )
            raise AuthenticationFailed(
                {"error": "invalid_credentials", "detail": "Invalid employee ID or password."}
            )

        # ── Check lockout ─────────────────────────────────────────────────
        if officer.is_locked:
            log_action(officer, AuditLog.Action.LOGIN_LOCKED, result="locked")
            remaining = int((officer.locked_until - timezone.now()).total_seconds() / 60)
            raise AuthenticationFailed(
                {
                    "error": "account_locked",
                    "detail": f"Account locked. Try again in {remaining} minute(s).",
                    "locked_until": officer.locked_until.isoformat(),
                }
            )

        # ── Verify password ───────────────────────────────────────────────
        if not officer.check_password(password) or not officer.is_active:
            officer.record_failed_login()
            log_action(officer, AuditLog.Action.LOGIN_FAILURE, result="wrong_password")

            max_attempts = getattr(settings, "MAX_FAILED_LOGIN_ATTEMPTS", 5)
            remaining_attempts = max(0, max_attempts - officer.failed_login_attempts)

            raise AuthenticationFailed(
                {
                    "error": "invalid_credentials",
                    "detail": "Invalid employee ID or password.",
                    "remaining_attempts": remaining_attempts,
                }
            )

        # ── Success ───────────────────────────────────────────────────────
        officer.reset_failed_login()
        officer.last_login = timezone.now()
        officer.save(update_fields=["last_login"])

        # Get the standard token data
        data = super().validate(attrs)

        # Append officer profile to login response
        data["officer"] = OfficerProfileSerializer(officer).data

        log_action(officer, AuditLog.Action.LOGIN_SUCCESS, result="success")
        return data

    @classmethod
    def get_token(cls, user):
        """Embed role into the JWT payload for fast permission checks."""
        token = super().get_token(user)
        token["employee_id"] = user.employee_id
        token["full_name"] = user.full_name
        token["role"] = user.role
        return token


# ── Login Request Serializer (for docs/validation) ────────────────────────────

class LoginRequestSerializer(serializers.Serializer):
    employee_id = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
