"""
ParkiPay — Billing Models
ControlNumber: the core transactional record with built-in
global duplicate-prevention via get_active_bill_for_plate().
"""

import random
import string

from django.conf import settings
from django.db import models
from django.utils import timezone

# ── Control Number Generator ──────────────────────────────────────────────────


def generate_control_number() -> str:
    """
    Generates a human-readable, unique control number.
    Format: PKP-YYYYMMDD-XXXXXX  (e.g. PKP-20260515-A3F9K2)
    """
    date_part = timezone.now().strftime("%Y%m%d")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"PKP-{date_part}-{random_part}"


# ── Status Choices ────────────────────────────────────────────────────────────


class BillStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    EXPIRED = "EXPIRED", "Expired"
    PAID = "PAID", "Paid"


# ── ControlNumber Model ───────────────────────────────────────────────────────


class ControlNumber(models.Model):
    """
    A single parking bill tied to one vehicle at one point in time.

    CORE RULE: only one ACTIVE ControlNumber may exist per plate_number
    across the entire system at any given time. This is enforced both at
    query time (get_active_bill_for_plate) and at model save time.
    """

    control_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        blank=True,  # Auto-generated in save()
    )
    plate_number = models.CharField(max_length=20, db_index=True)

    # FK to Vehicle — stored as FK for reporting; plate_number is denormalised
    # so the record stays intact even if the vehicle record changes.
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="control_numbers",
    )
    officer = models.ForeignKey(
        "accounts.Officer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bills_generated",
    )
    location = models.ForeignKey(
        "vehicles.ParkingLocation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="control_numbers",
    )

    amount_due = models.DecimalField(max_digits=10, decimal_places=2)

    generated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)

    status = models.CharField(
        max_length=10,
        choices=BillStatus.choices,
        default=BillStatus.ACTIVE,
        db_index=True,
    )

    # Notification status
    sms_sent = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    sms_error = models.CharField(max_length=300, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Control Number"
        verbose_name_plural = "Control Numbers"
        ordering = ["-generated_at"]
        indexes = [
            # Core duplicate-check index: plate + status + expiry
            models.Index(fields=["plate_number", "status", "expires_at"]),
            # Officer daily history
            models.Index(fields=["officer", "generated_at"]),
            # Expiry sweep by Celery task
            models.Index(fields=["status", "expires_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.pk:
            # Auto-generate control number if not provided
            if not self.control_number:
                self.control_number = generate_control_number()
            # Set expiry
            if not self.expires_at:
                hours = getattr(settings, "CONTROL_NUMBER_VALIDITY_HOURS", 5)
                from datetime import timedelta

                self.expires_at = timezone.now() + timedelta(hours=hours)
            # Normalise plate
            self.plate_number = self.plate_number.strip().upper().replace(" ", "")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.control_number} — {self.plate_number} [{self.status}]"

    @property
    def is_active(self) -> bool:
        """True only if status is ACTIVE AND has not expired (server-side)."""
        return self.status == BillStatus.ACTIVE and self.expires_at > timezone.now()

    @property
    def minutes_remaining(self) -> int:
        """Minutes until expiry; 0 if already expired."""
        delta = self.expires_at - timezone.now()
        return max(0, int(delta.total_seconds() / 60))


# ── Global Duplicate Prevention ───────────────────────────────────────────────


def get_active_bill_for_plate(plate_number: str):
    """
    THE central enforcement query.

    Returns the single ACTIVE ControlNumber for the given plate across
    ALL officers and ALL locations, or None if no active bill exists.

    This query is what makes duplicate billing impossible regardless of
    how many officers simultaneously try to bill the same vehicle.
    """
    return (
        ControlNumber.objects.filter(
            plate_number__iexact=plate_number.strip(),
            status=BillStatus.ACTIVE,
            expires_at__gt=timezone.now(),
        )
        .select_related("officer", "location", "vehicle")
        .first()
    )
