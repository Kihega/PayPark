"""
ParkiPay — Vehicles & Parking Locations Models
Phase 1: Seeded/mock national vehicle registry.
Phase 2: Live integration with BRELA/SUMATRA API.
"""

from django.db import models

# ── Vehicle Category ──────────────────────────────────────────────────────────


class VehicleCategory(models.TextChoices):
    MOTORCYCLE = "MOTORCYCLE", "Motorcycle / Bajaj"
    PRIVATE_CAR = "PRIVATE_CAR", "Private Car"
    MINIBUS = "MINIBUS", "Minibus (Daladala)"
    BUS = "BUS", "Bus / Coach"
    TRUCK = "TRUCK", "Truck / Lorry"
    GOVERNMENT = "GOVERNMENT", "Government Vehicle"


# ── Parking Location ──────────────────────────────────────────────────────────


class ParkingLocation(models.Model):
    """
    A government-registered parking area managed under ParkiPay.
    Fee amounts are per-session (not per-hour) for Phase 1.
    """

    name = models.CharField(max_length=120)
    region = models.CharField(max_length=60)
    district = models.CharField(max_length=60, blank=True)
    address = models.TextField(blank=True)

    # Coordinates for future map integration
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )

    # Parking fees (TZS) by vehicle category
    fee_motorcycle = models.DecimalField(max_digits=10, decimal_places=2, default=500)
    fee_private_car = models.DecimalField(max_digits=10, decimal_places=2, default=1000)
    fee_minibus = models.DecimalField(max_digits=10, decimal_places=2, default=2000)
    fee_bus = models.DecimalField(max_digits=10, decimal_places=2, default=3000)
    fee_truck = models.DecimalField(max_digits=10, decimal_places=2, default=5000)
    fee_government = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Parking Location"
        verbose_name_plural = "Parking Locations"
        ordering = ["region", "name"]

    def __str__(self):
        return f"{self.name}, {self.region}"

    def get_fee_for_category(self, category: str) -> float:
        """Return the parking fee for the given vehicle category."""
        fee_map = {
            VehicleCategory.MOTORCYCLE: self.fee_motorcycle,
            VehicleCategory.PRIVATE_CAR: self.fee_private_car,
            VehicleCategory.MINIBUS: self.fee_minibus,
            VehicleCategory.BUS: self.fee_bus,
            VehicleCategory.TRUCK: self.fee_truck,
            VehicleCategory.GOVERNMENT: self.fee_government,
        }
        return fee_map.get(category, self.fee_private_car)


# ── Vehicle ───────────────────────────────────────────────────────────────────


class Vehicle(models.Model):
    """
    National vehicle registry record.
    Phase 1: seeded from a government CSV/dataset.
    Phase 2: live lookup from SUMATRA/BRELA API.
    """

    plate_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Normalised to UPPERCASE, no spaces.",
    )

    # Owner details
    owner_name = models.CharField(max_length=150)
    owner_phone = models.CharField(
        max_length=20,
        help_text="Must be a valid Tanzanian mobile number (+255...).",
    )
    owner_email = models.EmailField(blank=True)

    # Vehicle details
    make = models.CharField(max_length=60, blank=True, help_text="e.g. Toyota")
    model = models.CharField(max_length=60, blank=True, help_text="e.g. Corolla")
    color = models.CharField(max_length=40, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    category = models.CharField(
        max_length=20,
        choices=VehicleCategory.choices,
        default=VehicleCategory.PRIVATE_CAR,
    )

    # Registration
    registration_date = models.DateField(null=True, blank=True)
    is_valid = models.BooleanField(
        default=True,
        help_text="False = unregistered, stolen, or flagged.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"
        ordering = ["plate_number"]

    def __str__(self):
        return f"{self.plate_number} — {self.owner_name} ({self.make} {self.model})"

    def save(self, *args, **kwargs):
        # Always normalise plate number
        self.plate_number = self.plate_number.strip().upper().replace(" ", "")
        super().save(*args, **kwargs)
