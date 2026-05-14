"""
ParkiPay Test Suite
Covers: authentication, plate lookup, control number generation,
        duplicate prevention, and expiry enforcement.
"""
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from datetime import timedelta

from accounts.models import Officer, OfficerRole
from vehicles.models import Vehicle, ParkingLocation, VehicleCategory
from billing.models import ControlNumber, BillStatus, get_active_bill_for_plate


def make_officer(**kwargs):
    defaults = dict(
        employee_id="OFF001", full_name="Test Officer", role=OfficerRole.FIELD_OFFICER
    )
    defaults.update(kwargs)
    o = Officer(**defaults)
    o.set_password("testpass123")
    o.save()
    return o


def make_vehicle(**kwargs):
    defaults = dict(
        plate_number="T 123 ABC",
        owner_name="Juma Hassan",
        owner_phone="+255712000001",
        owner_email="juma@test.com",
        make="Toyota", model="Corolla", color="White",
        category=VehicleCategory.PRIVATE,
        is_valid=True,
    )
    defaults.update(kwargs)
    return Vehicle.objects.create(**defaults)


def make_location(**kwargs):
    defaults = dict(name="Parking Posta", region="Dar es Salaam", district="Ilala",
                    fee_private=2000, fee_commercial=5000)
    defaults.update(kwargs)
    return ParkingLocation.objects.create(**defaults)


# ─────────────────────────────────────────────────────────────────────────────
# Auth Tests
# ─────────────────────────────────────────────────────────────────────────────

class LoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.officer = make_officer()
        self.url = "/api/auth/login/"

    def test_valid_login_returns_tokens(self):
        res = self.client.post(self.url, {
            "employee_id": "OFF001", "password": "testpass123"
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertIn("officer", res.data)

    def test_invalid_password_returns_401(self):
        res = self.client.post(self.url, {
            "employee_id": "OFF001", "password": "wrongpass"
        })
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_employee_id_returns_401(self):
        res = self.client.post(self.url, {
            "employee_id": "NOBODY", "password": "pass"
        })
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_account_locked_after_5_failures(self):
        for _ in range(5):
            self.client.post(self.url, {"employee_id": "OFF001", "password": "wrong"})
        self.officer.refresh_from_db()
        self.assertTrue(self.officer.is_locked)

    def test_locked_account_cannot_login(self):
        self.officer.locked_until = timezone.now() + timedelta(minutes=10)
        self.officer.save()
        res = self.client.post(self.url, {
            "employee_id": "OFF001", "password": "testpass123"
        })
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("locked", res.data.get("detail", "").lower())

    def test_jwt_payload_contains_role(self):
        res = self.client.post(self.url, {
            "employee_id": "OFF001", "password": "testpass123"
        })
        self.assertEqual(res.data["officer"]["role"], OfficerRole.FIELD_OFFICER)

    def test_me_endpoint_requires_auth(self):
        res = self.client.get("/api/auth/me/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_endpoint_returns_profile(self):
        self.client.force_authenticate(user=self.officer)
        res = self.client.get("/api/auth/me/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["employee_id"], "OFF001")


# ─────────────────────────────────────────────────────────────────────────────
# Vehicle Lookup Tests
# ─────────────────────────────────────────────────────────────────────────────

class VehicleLookupTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.officer = make_officer()
        self.client.force_authenticate(user=self.officer)
        self.vehicle = make_vehicle()
        self.url = "/api/vehicles/lookup/"

    def test_valid_plate_returns_vehicle_data(self):
        res = self.client.get(self.url, {"plate": "T 123 ABC"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["plate_number"], "T 123 ABC")
        self.assertEqual(res.data["owner_name"], "Juma Hassan")
        self.assertIn("owner_phone", res.data)

    def test_lookup_is_case_insensitive(self):
        res = self.client.get(self.url, {"plate": "t 123 abc"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unknown_plate_returns_404(self):
        res = self.client.get(self.url, {"plate": "T 999 ZZZ"})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(res.data["error"], "plate_not_found")

    def test_missing_plate_param_returns_400(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_lookup_blocked(self):
        self.client.logout()
        res = self.client.get(self.url, {"plate": "T 123 ABC"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# ─────────────────────────────────────────────────────────────────────────────
# Control Number Generation Tests  (Core duplicate-prevention logic)
# ─────────────────────────────────────────────────────────────────────────────

class BillGenerationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.officer1 = make_officer(employee_id="OFF001", full_name="Officer One")
        self.officer2 = make_officer(employee_id="OFF002", full_name="Officer Two")
        self.vehicle = make_vehicle()
        self.location = make_location()
        self.url = "/api/billing/generate/"

    @patch("billing.views.send_sms_notification.delay")
    @patch("billing.views.send_email_notification.delay")
    def test_first_bill_creates_successfully(self, mock_email, mock_sms):
        self.client.force_authenticate(user=self.officer1)
        res = self.client.post(self.url, {
            "plate_number": "T 123 ABC",
            "location_id": self.location.id,
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("control_number", res.data)
        self.assertTrue(res.data["control_number"].startswith("PKP-"))
        mock_sms.assert_called_once()
        mock_email.assert_called_once()

    @patch("billing.views.send_sms_notification.delay")
    @patch("billing.views.send_email_notification.delay")
    def test_duplicate_bill_by_same_officer_blocked(self, mock_email, mock_sms):
        """Same officer cannot bill same plate twice within 5 hrs."""
        self.client.force_authenticate(user=self.officer1)
        self.client.post(self.url, {"plate_number": "T 123 ABC"})
        res = self.client.post(self.url, {"plate_number": "T 123 ABC"})
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(res.data["error"], "active_bill_exists")

    @patch("billing.views.send_sms_notification.delay")
    @patch("billing.views.send_email_notification.delay")
    def test_duplicate_bill_by_different_officer_blocked(self, mock_email, mock_sms):
        """
        CORE TEST: A DIFFERENT officer cannot bill the same plate
        if an active bill already exists — regardless of who issued it.
        This is the primary duplicate-prevention guarantee.
        """
        # Officer 1 bills the vehicle
        self.client.force_authenticate(user=self.officer1)
        res1 = self.client.post(self.url, {"plate_number": "T 123 ABC"})
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Officer 2 attempts to bill the same vehicle
        self.client.force_authenticate(user=self.officer2)
        res2 = self.client.post(self.url, {"plate_number": "T 123 ABC"})

        self.assertEqual(res2.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(res2.data["error"], "active_bill_exists")
        # Response must include info about who issued it
        self.assertIn("existing_bill", res2.data)
        self.assertEqual(
            res2.data["existing_bill"]["issued_by_id"], "OFF001"
        )

    @patch("billing.views.send_sms_notification.delay")
    @patch("billing.views.send_email_notification.delay")
    def test_new_bill_allowed_after_expiry(self, mock_email, mock_sms):
        """A new bill CAN be generated after the previous one expires."""
        # Create an already-expired bill directly
        ControlNumber.objects.create(
            plate_number="T 123 ABC",
            vehicle=self.vehicle,
            officer=self.officer1,
            location=self.location,
            amount_due=2000,
            status=BillStatus.EXPIRED,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        self.client.force_authenticate(user=self.officer2)
        res = self.client.post(self.url, {"plate_number": "T 123 ABC"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_unknown_plate_returns_404(self):
        self.client.force_authenticate(user=self.officer1)
        res = self.client.post(self.url, {"plate_number": "T 999 ZZZ"})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_request_blocked(self):
        res = self.client.post(self.url, {"plate_number": "T 123 ABC"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_control_number_expires_in_5_hours(self):
        """expires_at must be exactly 5 hours from generated_at."""
        bill = ControlNumber.objects.create(
            plate_number="T 123 ABC",
            vehicle=self.vehicle,
            officer=self.officer1,
            location=self.location,
            amount_due=2000,
        )
        delta = bill.expires_at - bill.generated_at
        self.assertAlmostEqual(delta.total_seconds(), 5 * 3600, delta=5)


# ─────────────────────────────────────────────────────────────────────────────
# Expiry Task Tests
# ─────────────────────────────────────────────────────────────────────────────

class ExpiryTaskTests(TestCase):
    def setUp(self):
        self.officer = make_officer()
        self.vehicle = make_vehicle()
        self.location = make_location()

    def test_expire_control_numbers_task(self):
        from billing.tasks import expire_control_numbers

        # Bill that should be expired (past expires_at)
        expired_bill = ControlNumber.objects.create(
            plate_number="T 123 ABC",
            vehicle=self.vehicle,
            officer=self.officer,
            location=self.location,
            amount_due=2000,
            status=BillStatus.ACTIVE,
        )
        expired_bill.expires_at = timezone.now() - timedelta(hours=1)
        expired_bill.save()

        # Bill that should remain ACTIVE
        active_bill = ControlNumber.objects.create(
            plate_number="T 456 DEF",
            vehicle=self.vehicle,
            officer=self.officer,
            location=self.location,
            amount_due=2000,
            status=BillStatus.ACTIVE,
        )

        result = expire_control_numbers()

        expired_bill.refresh_from_db()
        active_bill.refresh_from_db()

        self.assertEqual(expired_bill.status, BillStatus.EXPIRED)
        self.assertEqual(active_bill.status, BillStatus.ACTIVE)
        self.assertEqual(result["expired"], 1)


# ─────────────────────────────────────────────────────────────────────────────
# Billing History Tests
# ─────────────────────────────────────────────────────────────────────────────

class BillingHistoryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.officer = make_officer()
        self.client.force_authenticate(user=self.officer)
        self.vehicle = make_vehicle()
        self.location = make_location()

    def test_history_returns_only_own_bills(self):
        other = make_officer(employee_id="OFF002", full_name="Other")
        ControlNumber.objects.create(
            plate_number="T 123 ABC", vehicle=self.vehicle,
            officer=self.officer, location=self.location, amount_due=2000,
        )
        ControlNumber.objects.create(
            plate_number="T 456 DEF", vehicle=self.vehicle,
            officer=other, location=self.location, amount_due=2000,
        )
        res = self.client.get("/api/billing/history/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["total"], 1)

    def test_history_requires_auth(self):
        self.client.logout()
        res = self.client.get("/api/billing/history/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# ─────────────────────────────────────────────────────────────────────────────
# get_active_bill_for_plate unit test
# ─────────────────────────────────────────────────────────────────────────────

class GetActiveBillTests(TestCase):
    def setUp(self):
        self.officer = make_officer()
        self.vehicle = make_vehicle()
        self.location = make_location()

    def test_returns_none_when_no_bills(self):
        result = get_active_bill_for_plate("T 123 ABC")
        self.assertIsNone(result)

    def test_returns_active_bill(self):
        bill = ControlNumber.objects.create(
            plate_number="T 123 ABC", vehicle=self.vehicle,
            officer=self.officer, location=self.location, amount_due=2000,
        )
        result = get_active_bill_for_plate("T 123 ABC")
        self.assertEqual(result.id, bill.id)

    def test_ignores_expired_bills(self):
        bill = ControlNumber.objects.create(
            plate_number="T 123 ABC", vehicle=self.vehicle,
            officer=self.officer, location=self.location, amount_due=2000,
            status=BillStatus.EXPIRED,
        )
        bill.expires_at = timezone.now() - timedelta(hours=1)
        bill.save()
        result = get_active_bill_for_plate("T 123 ABC")
        self.assertIsNone(result)

    def test_case_insensitive_match(self):
        ControlNumber.objects.create(
            plate_number="T 123 ABC", vehicle=self.vehicle,
            officer=self.officer, location=self.location, amount_due=2000,
        )
        result = get_active_bill_for_plate("t 123 abc")
        self.assertIsNotNone(result)
