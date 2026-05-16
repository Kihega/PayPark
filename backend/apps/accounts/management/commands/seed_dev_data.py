"""
ParkiPay — Management Command: seed_dev_data

Creates realistic test fixtures for local development and CI:
  - 5 Parking Locations (Dar es Salaam, Dodoma, Mwanza)
  - 3 Officers (1 admin, 1 supervisor, 1 field officer)
  - 10 Vehicles (mixed categories)

Usage:
    python manage.py seed_dev_data
    python manage.py seed_dev_data --reset   (clears existing data first)
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Officer, OfficerRole
from apps.vehicles.models import ParkingLocation, Vehicle, VehicleCategory

LOCATIONS = [
    {
        "name": "Kariakoo Bus Terminal",
        "region": "Dar es Salaam",
        "district": "Ilala",
        "address": "Msimbazi Street, Kariakoo",
        "latitude": "-6.8150",
        "longitude": "39.2690",
        "fee_motorcycle": 500,
        "fee_private_car": 1000,
        "fee_minibus": 2000,
        "fee_bus": 3000,
        "fee_truck": 5000,
    },
    {
        "name": "Posta / Azikiwe Street Parking",
        "region": "Dar es Salaam",
        "district": "Ilala",
        "address": "Azikiwe Street, City Centre",
        "latitude": "-6.8106",
        "longitude": "39.2900",
        "fee_motorcycle": 500,
        "fee_private_car": 2000,
        "fee_minibus": 3000,
        "fee_bus": 4000,
        "fee_truck": 6000,
    },
    {
        "name": "Ubungo Interchange Parking",
        "region": "Dar es Salaam",
        "district": "Ubungo",
        "address": "Morogoro Road, Ubungo",
        "latitude": "-6.7920",
        "longitude": "39.2170",
        "fee_motorcycle": 500,
        "fee_private_car": 1000,
        "fee_minibus": 2000,
        "fee_bus": 3000,
        "fee_truck": 5000,
    },
    {
        "name": "Dodoma Central Parking",
        "region": "Dodoma",
        "district": "Dodoma Urban",
        "address": "Jakaya Kikwete Road, Dodoma",
        "latitude": "-6.1722",
        "longitude": "35.7395",
        "fee_motorcycle": 300,
        "fee_private_car": 800,
        "fee_minibus": 1500,
        "fee_bus": 2500,
        "fee_truck": 4000,
    },
    {
        "name": "Mwanza Ferry Terminal",
        "region": "Mwanza",
        "district": "Nyamagana",
        "address": "Port Road, Mwanza",
        "latitude": "-2.5164",
        "longitude": "32.8997",
        "fee_motorcycle": 500,
        "fee_private_car": 1000,
        "fee_minibus": 2000,
        "fee_bus": 3000,
        "fee_truck": 5000,
    },
]

OFFICERS = [
    {
        "employee_id": "ADMIN001",
        "full_name": "Ibrahim Mwangi Hassan",
        "phone": "+255711000001",
        "email": "admin@parkipay.go.tz",
        "role": OfficerRole.ADMIN,
        "password": "ParkiPay@Admin2026!",
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "employee_id": "SUP001",
        "full_name": "Fatuma Ally Kimaro",
        "phone": "+255722000002",
        "email": "fatuma.ally@parkipay.go.tz",
        "role": OfficerRole.SUPERVISOR,
        "password": "ParkiPay@Super2026!",
        "location_index": 0,  # Kariakoo
    },
    {
        "employee_id": "OF001",
        "full_name": "Juma Rashidi Mwaura",
        "phone": "+255733000003",
        "email": "juma.rashidi@parkipay.go.tz",
        "role": OfficerRole.FIELD_OFFICER,
        "password": "ParkiPay@Field2026!",
        "location_index": 0,  # Kariakoo
    },
    {
        "employee_id": "OF002",
        "full_name": "Grace Ndunguru Petro",
        "phone": "+255744000004",
        "email": "grace.ndunguru@parkipay.go.tz",
        "role": OfficerRole.FIELD_OFFICER,
        "password": "ParkiPay@Field2026!",
        "location_index": 1,  # Posta
    },
    {
        "employee_id": "OF003",
        "full_name": "Amos Kileo Mwakibete",
        "phone": "+255755000005",
        "email": "amos.kileo@parkipay.go.tz",
        "role": OfficerRole.FIELD_OFFICER,
        "password": "ParkiPay@Field2026!",
        "location_index": 3,  # Dodoma
    },
]

VEHICLES = [
    {"plate": "T123ABC", "owner": "Chakula Enterprises Ltd", "phone": "+255711100001",
     "make": "Toyota", "model": "Hiace", "color": "White", "year": 2019,
     "category": VehicleCategory.MINIBUS},
    {"plate": "T456DEF", "owner": "Amani Hassan", "phone": "+255722200002",
     "make": "Toyota", "model": "Corolla", "color": "Silver", "year": 2021,
     "category": VehicleCategory.PRIVATE_CAR},
    {"plate": "T789GHI", "owner": "Logistics TZ Co.", "phone": "+255733300003",
     "make": "Isuzu", "model": "NQR", "color": "Blue", "year": 2018,
     "category": VehicleCategory.TRUCK},
    {"plate": "T321JKL", "owner": "Zawadi Petro", "phone": "+255744400004",
     "make": "Honda", "model": "CB125", "color": "Red", "year": 2022,
     "category": VehicleCategory.MOTORCYCLE},
    {"plate": "T654MNO", "owner": "Dar Express Bus Co.", "phone": "+255755500005",
     "make": "Yutong", "model": "ZK6122H", "color": "Orange", "year": 2020,
     "category": VehicleCategory.BUS},
    {"plate": "T987PQR", "owner": "Baraka Ally", "phone": "+255766600006",
     "make": "Suzuki", "model": "Alto", "color": "Green", "year": 2020,
     "category": VehicleCategory.PRIVATE_CAR},
    {"plate": "SMZ001", "owner": "Zanzibar Port Authority", "phone": "+255777700007",
     "make": "Toyota", "model": "Land Cruiser", "color": "White", "year": 2023,
     "category": VehicleCategory.GOVERNMENT},
    {"plate": "T112STU", "owner": "Neema Mchome", "phone": "+255788800008",
     "make": "Bajaj", "model": "RE", "color": "Yellow", "year": 2021,
     "category": VehicleCategory.MOTORCYCLE},
    {"plate": "T334VWX", "owner": "Safari Tours Ltd", "phone": "+255799900009",
     "make": "Toyota", "model": "Land Cruiser", "color": "Beige", "year": 2022,
     "category": VehicleCategory.PRIVATE_CAR},
    {"plate": "T556YZA", "owner": "Ndoto Trucking", "phone": "+255700000010",
     "make": "Mercedes", "model": "Actros", "color": "Red", "year": 2017,
     "category": VehicleCategory.TRUCK},
]


class Command(BaseCommand):
    help = "Seed the database with development / demo data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing seed data before inserting (non-destructive to real data).",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n🌱  ParkiPay Dev Data Seed\n"))

        with transaction.atomic():
            if options["reset"]:
                self.stdout.write("  → Clearing existing data...")
                Vehicle.objects.all().delete()
                Officer.objects.filter(
                    employee_id__in=[o["employee_id"] for o in OFFICERS]).delete()
                ParkingLocation.objects.all().delete()
                self.stdout.write(self.style.WARNING(
                    "  → Existing seed data cleared.\n"))

            # ── Parking Locations ─────────────────────────────────────────────
            self.stdout.write("  → Creating parking locations...")
            created_locations = []
            for loc_data in LOCATIONS:
                loc, created = ParkingLocation.objects.get_or_create(
                    name=loc_data["name"],
                    region=loc_data["region"],
                    defaults=loc_data,
                )
                created_locations.append(loc)
                status = self.style.SUCCESS(
                    "created") if created else "already exists"
                self.stdout.write(
                    f"     {'✅' if created else '⏭ '} {loc.name} — {status}")

            # ── Officers ──────────────────────────────────────────────────────
            self.stdout.write("\n  → Creating officers...")
            for off_data in OFFICERS:
                location = None
                if "location_index" in off_data:
                    location = created_locations[off_data.pop(
                        "location_index")]

                password = off_data.pop("password")
                is_superuser = off_data.pop("is_superuser", False)
                is_staff = off_data.pop("is_staff", False)

                officer, created = Officer.objects.get_or_create(
                    employee_id=off_data["employee_id"],
                    defaults={
                        **off_data,
                        "location": location,
                        "is_superuser": is_superuser,
                        "is_staff": is_staff,
                    },
                )
                if created:
                    officer.set_password(password)
                    officer.save()
                status = self.style.SUCCESS(
                    "created") if created else "already exists"
                self.stdout.write(
                    f"     {'✅' if created else '⏭ '} {officer.full_name}"
                    f" [{officer.role}]  login: {officer.employee_id} / {password if created else '(unchanged)'}"
                    f" — {status}"
                )

            # ── Vehicles ──────────────────────────────────────────────────────
            self.stdout.write("\n  → Creating vehicles...")
            for v in VEHICLES:
                vehicle, created = Vehicle.objects.get_or_create(
                    plate_number=v["plate"],
                    defaults={
                        "owner_name": v["owner"],
                        "owner_phone": v["phone"],
                        "make": v["make"],
                        "model": v["model"],
                        "color": v["color"],
                        "year": v["year"],
                        "category": v["category"],
                    },
                )
                status = self.style.SUCCESS(
                    "created") if created else "already exists"
                self.stdout.write(
                    f"     {'✅' if created else '⏭ '} {vehicle.plate_number}"
                    f" — {vehicle.make} {vehicle.model} ({vehicle.category}) — {status}"
                )

        self.stdout.write(self.style.SUCCESS(
            f"\n✅  Seeding complete!\n"
            f"    Locations : {len(LOCATIONS)}\n"
            f"    Officers  : {len(OFFICERS)}\n"
            f"    Vehicles  : {len(VEHICLES)}\n\n"
            f"    Admin login → employee_id: ADMIN001 / password: ParkiPay@Admin2026!\n"
            f"    Django admin → http://localhost:8000/admin/\n"
        ))
