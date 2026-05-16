"""
ParkiPay — Auth Tests (Sprint 1)
Tests: login success, wrong password, lockout, token refresh, logout, /me.
Run with: pytest apps/accounts/tests/
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import Officer, OfficerRole

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def officer(db):
    return Officer.objects.create_user(
        employee_id="TZ-TEST-001",
        password="SecurePass123!",
        full_name="Amina Rashidi",
        role=OfficerRole.FIELD_OFFICER,
    )


@pytest.fixture
def tokens(api, officer):
    """Return access + refresh tokens for the test officer."""
    url = reverse("auth-login")
    resp = api.post(
        url, {"employee_id": officer.employee_id, "password": "SecurePass123!"})
    assert resp.status_code == 200, resp.data
    return resp.data["access"], resp.data["refresh"]


# ── Login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    def test_valid_credentials_returns_tokens_and_profile(self, api, officer):
        url = reverse("auth-login")
        resp = api.post(
            url, {"employee_id": officer.employee_id, "password": "SecurePass123!"})
        assert resp.status_code == 200
        assert "access" in resp.data
        assert "refresh" in resp.data
        assert resp.data["officer"]["employee_id"] == officer.employee_id
        assert resp.data["officer"]["role"] == OfficerRole.FIELD_OFFICER

    def test_wrong_password_returns_401(self, api, officer):
        url = reverse("auth-login")
        resp = api.post(
            url, {"employee_id": officer.employee_id, "password": "WrongPassword!"})
        assert resp.status_code == 401
        assert resp.data["error"] == "invalid_credentials"
        assert "remaining_attempts" in resp.data

    def test_unknown_employee_id_returns_401(self, api, db):
        url = reverse("auth-login")
        resp = api.post(
            url, {"employee_id": "GHOST-999", "password": "anything"})
        assert resp.status_code == 401
        assert resp.data["error"] == "invalid_credentials"

    def test_missing_fields_returns_400(self, api, db):
        url = reverse("auth-login")
        resp = api.post(url, {"employee_id": "TZ-TEST-001"})
        # No password field
        assert resp.status_code in (400, 401)

    def test_login_increments_failed_attempts(self, api, officer):
        url = reverse("auth-login")
        api.post(
            url, {"employee_id": officer.employee_id, "password": "wrong"})
        officer.refresh_from_db()
        assert officer.failed_login_attempts == 1

    def test_successful_login_resets_failed_attempts(self, api, officer):
        # Create some existing failures
        officer.failed_login_attempts = 3
        officer.save()

        url = reverse("auth-login")
        resp = api.post(
            url, {"employee_id": officer.employee_id, "password": "SecurePass123!"})
        assert resp.status_code == 200
        officer.refresh_from_db()
        assert officer.failed_login_attempts == 0


# ── Account Lockout ───────────────────────────────────────────────────────────

class TestLockout:
    def test_account_locks_after_5_failed_attempts(self, api, officer):
        url = reverse("auth-login")
        for _ in range(5):
            api.post(
                url, {"employee_id": officer.employee_id, "password": "wrong"})

        # 6th attempt should be blocked with lockout error
        resp = api.post(
            url, {"employee_id": officer.employee_id, "password": "wrong"})
        assert resp.status_code == 401
        assert resp.data["error"] == "account_locked"
        assert "locked_until" in resp.data

    def test_locked_account_rejects_correct_password(self, api, officer):
        """Even the correct password is rejected while account is locked."""
        from datetime import timedelta

        from django.utils import timezone
        officer.failed_login_attempts = 5
        officer.locked_until = timezone.now() + timedelta(minutes=10)
        officer.save()

        url = reverse("auth-login")
        resp = api.post(
            url, {"employee_id": officer.employee_id, "password": "SecurePass123!"})
        assert resp.status_code == 401
        assert resp.data["error"] == "account_locked"


# ── Token Refresh ─────────────────────────────────────────────────────────────

class TestTokenRefresh:
    def test_valid_refresh_returns_new_access_token(self, api, officer, tokens):
        access, refresh = tokens
        url = reverse("auth-refresh")
        resp = api.post(url, {"refresh": refresh})
        assert resp.status_code == 200
        assert "access" in resp.data
        # New access token must be different from original
        assert resp.data["access"] != access

    def test_invalid_refresh_token_returns_401(self, api, db):
        url = reverse("auth-refresh")
        resp = api.post(url, {"refresh": "not.a.valid.token"})
        assert resp.status_code == 401


# ── Logout ────────────────────────────────────────────────────────────────────

class TestLogout:
    def test_logout_blacklists_refresh_token(self, api, officer, tokens):
        access, refresh = tokens
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        url = reverse("auth-logout")
        resp = api.post(url, {"refresh": refresh})
        assert resp.status_code == 200

        # Blacklisted token must not work
        refresh_url = reverse("auth-refresh")
        retry = api.post(refresh_url, {"refresh": refresh})
        assert retry.status_code == 401

    def test_logout_requires_auth(self, api, db):
        url = reverse("auth-logout")
        resp = api.post(url, {"refresh": "any"})
        assert resp.status_code == 401

    def test_logout_without_refresh_token_returns_400(self, api, officer, tokens):
        access, _ = tokens
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        url = reverse("auth-logout")
        resp = api.post(url, {})
        assert resp.status_code == 400
        assert resp.data["error"] == "refresh_required"


# ── /me Endpoint ──────────────────────────────────────────────────────────────

class TestMeEndpoint:
    def test_me_returns_officer_profile(self, api, officer, tokens):
        access, _ = tokens
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        url = reverse("auth-me")
        resp = api.get(url)
        assert resp.status_code == 200
        assert resp.data["employee_id"] == officer.employee_id
        assert resp.data["full_name"] == officer.full_name
        assert resp.data["role"] == officer.role

    def test_me_requires_auth(self, api, db):
        url = reverse("auth-me")
        resp = api.get(url)
        assert resp.status_code == 401


# ── Health Check ──────────────────────────────────────────────────────────────

class TestHealthCheck:
    def test_health_returns_ok(self, api, db):
        url = reverse("health-check")
        resp = api.get(url)
        assert resp.status_code == 200
        assert resp.data["status"] == "ok"
        assert resp.data["service"] == "ParkiPay API"
        assert "timestamp" in resp.data
