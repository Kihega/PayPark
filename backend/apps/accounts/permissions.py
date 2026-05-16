"""ParkiPay — Role-Based DRF Permission Classes"""

from rest_framework.permissions import BasePermission

from apps.accounts.models import OfficerRole


class IsFieldOfficer(BasePermission):
    """Allow any authenticated officer (all roles can act as field officers)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active)


class IsSupervisor(BasePermission):
    """Allow SUPERVISOR and ADMIN roles only."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (OfficerRole.SUPERVISOR, OfficerRole.ADMIN)
        )


class IsAdmin(BasePermission):
    """Allow ADMIN role only."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == OfficerRole.ADMIN
