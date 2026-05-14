import random
import string
from datetime import timedelta
from django.db import models
from django.utils import timezone


def generate_control_number():
    """Generate a unique control number: PKP-YYYYMMDD-XXXXXX"""
    date_part = timezone.now().strftime("%Y%m%d")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"PKP-{date_part}-{random_part}"


class BillStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    EXPIRED = "EXPIRED", "Expired"
    PAID = "PAID", "Paid"


class ControlNumber(models.Model):
    control_number = models.CharField(max_length=30, unique=True, db_index=True)
    plate_number = models.CharField(max_length=20, db_index=True)
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.SET_NULL,
        null=True,
        related_name="bills",
    )
    officer = models.ForeignKey(
        "accounts.Officer",
        on_delete=models.SET_NULL,
        null=True,
        related_name="bills_generated",
    )
    location = models.ForeignKey(
        "vehicles.ParkingLocation",
        on_delete=models.SET_NULL,
        null=True,
        related_name="bills",
    )
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    generated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=10, choices=BillStatus.choices, default=BillStatus.ACTIVE, db_index=True
    )
    sms_sent = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Control Number"
        verbose_name_plural = "Control Numbers"
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["plate_number", "status"]),
            models.Index(fields=["status", "expires_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.pk:
            if not self.control_number:
                self.control_number = generate_control_number()
            if not self.expires_at:
                self.expires_at = timezone.now() + timedelta(hours=5)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.control_number} — {self.plate_number} ({self.status})"

    @property
    def is_active(self):
        return self.status == BillStatus.ACTIVE and self.expires_at > timezone.now()


def get_active_bill_for_plate(plate_number):
    """
    Global check: return the ACTIVE ControlNumber for this plate
    across ALL officers and locations, or None if none exists.
    This is the core duplicate-prevention query.
    """
    return ControlNumber.objects.filter(
        plate_number__iexact=plate_number,
        status=BillStatus.ACTIVE,
        expires_at__gt=timezone.now(),
    ).select_related("officer", "location").first()
