"""ParkiPay — Django Admin: Vehicles & Locations"""
from django.contrib import admin
from apps.vehicles.models import Vehicle, ParkingLocation


@admin.register(ParkingLocation)
class ParkingLocationAdmin(admin.ModelAdmin):
    list_display = ["name", "region", "district", "is_active", "fee_private_car", "fee_motorcycle"]
    list_filter = ["region", "is_active"]
    search_fields = ["name", "region", "district"]


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ["plate_number", "owner_name", "owner_phone", "make", "model", "category", "is_valid"]
    list_filter = ["category", "is_valid"]
    search_fields = ["plate_number", "owner_name", "owner_phone"]
    readonly_fields = ["created_at", "updated_at"]
