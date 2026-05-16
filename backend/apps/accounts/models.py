"""
ParkiPay — Accounts Models
Officer: Custom AbstractBaseUser authenticated by employee_id + password.
AuditLog: Immutable record of every security-relevant action.
"""

from django.conf import settings
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.db import models
from django.utils import timezone

# ── Officer Manager ───────────────────────────────────────────────────────────


class OfficerManager(BaseUserManager):
    def create_user(self, employee_id, password, **extra_fields):
        if not employee_id:
            raise ValueError("Employee ID is required.")
        if not password:
            raise ValueError("Password is required.")
        officer = self.model(employee_id=employee_id, **extra_fields)
        officer.set_password(password)
        officer.save(using=self._db)
        return officer

    def create_superuser(self, employee_id, password, **extra_fields):
        extra_fields.setdefault("role", OfficerRole.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(employee_id, password, **extra_fields)


# ── Choices ───────────────────────────────────────────────────────────────────


class OfficerRole(models.TextChoices):
    FIELD_OFFICER = "FIELD_OFFICER", "Field Officer"
    SUPERVISOR = "SUPERVISOR", "Supervisor"
    ADMIN = "ADMIN", "Administrator"


# ── Officer Model ─────────────────────────────────────────────────────────────


class Officer(AbstractBaseUser, PermissionsMixin):
    """
    Government field officer who uses the ParkiPay mobile app.
    Authenticated via employee_id (not username or email).
    """

    employee_id = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Government-issued employee ID. Used for login.",
    )
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    role = models.CharField(
        max_length=20,
        choices=OfficerRole.choices,
        default=OfficerRole.FIELD_OFFICER,
    )

    # Assigned default parking location (can be overridden per-bill)
    location = models.ForeignKey(
        "vehicles.ParkingLocation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="officers",
    )

    # ── Account state ─────────────────────────────────────────────────────
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Required for Django admin

    # ── Lockout mechanism ─────────────────────────────────────────────────
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = OfficerManager()

    USERNAME_FIELD = "employee_id"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        verbose_name = "Officer"
        verbose_name_plural = "Officers"
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.employee_id}) — {self.role}"

    # ── Lockout helpers ───────────────────────────────────────────────────

    @property
    def is_locked(self):
        """Return True if the account is currently locked out."""
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False

    def record_failed_login(self):
        """Increment failure counter; lock account if threshold reached."""
        max_attempts = getattr(settings, "MAX_FAILED_LOGIN_ATTEMPTS", 5)
        lockout_minutes = getattr(settings, "LOCKOUT_DURATION_MINUTES", 15)

        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            from datetime import timedelta

            self.locked_until = timezone.now() + timedelta(minutes=lockout_minutes)
        self.save(update_fields=["failed_login_attempts", "locked_until"])

    def reset_failed_login(self):
        """Clear failure counter on successful login."""
        if self.failed_login_attempts > 0 or self.locked_until:
            self.failed_login_attempts = 0
            self.locked_until = None
            self.save(update_fields=["failed_login_attempts", "locked_until"])


# ── Audit Log ─────────────────────────────────────────────────────────────────


class AuditLog(models.Model):
    """
    Immutable record of every security-relevant action in the system.
    Written on login, logout, bill generation, duplicate attempts, etc.
    """

    class Action(models.TextChoices):
        LOGIN_SUCCESS = "LOGIN_SUCCESS", "Login Success"
        LOGIN_FAILURE = "LOGIN_FAILURE", "Login Failure"
        LOGIN_LOCKED = "LOGIN_LOCKED", "Login Attempt — Account Locked"
        LOGOUT = "LOGOUT", "Logout"
        TOKEN_REFRESH = "TOKEN_REFRESH", "Token Refresh"
        BILL_GENERATED = "BILL_GENERATED", "Bill Generated"
        BILL_DUPLICATE_BLOCKED = "BILL_DUPLICATE_BLOCKED", "Duplicate Bill Blocked"
        VEHICLE_LOOKUP = "VEHICLE_LOOKUP", "Vehicle Lookup"
        PLATE_NOT_FOUND = "PLATE_NOT_FOUND", "Plate Not Found"

    officer = models.ForeignKey(
        Officer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=40, choices=Action.choices, db_index=True)
    plate_number = models.CharField(max_length=20, blank=True, db_index=True)
    control_number = models.CharField(max_length=30, blank=True)
    result = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    extra = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["officer", "timestamp"]),
            models.Index(fields=["action", "timestamp"]),
        ]

    def __str__(self):
        officer_str = str(self.officer) if self.officer else "Anonymous"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {officer_str} — {self.action}"


# ── Helper function ───────────────────────────────────────────────────────────


def log_action(officer, action, *, plate_number="", control_number="", result="", request=None, **extra):
    """
    Convenience wrapper to write to the audit log.
    Call from any view; does not raise exceptions.
    """
    ip = None
    ua = ""
    if request:
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = x_forwarded.split(",")[0].strip() if x_forwarded else request.META.get("REMOTE_ADDR")
        ua = request.META.get("HTTP_USER_AGENT", "")[:300]

    try:
        AuditLog.objects.create(
            officer=officer if isinstance(officer, Officer) else None,
            action=action,
            plate_number=plate_number,
            control_number=control_number,
            result=result,
            ip_address=ip,
            user_agent=ua,
            extra=extra,
        )
    except Exception:
        # Audit log failure must NEVER break the main flow
        pass
