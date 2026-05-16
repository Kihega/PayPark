"""
ParkiPay — Auth Views
POST /api/auth/login/     → JWT login (employee_id + password)
POST /api/auth/refresh/   → Rotate refresh token
POST /api/auth/logout/    → Blacklist refresh token
GET  /api/auth/me/        → Officer profile
"""

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.models import AuditLog, log_action
from apps.accounts.serializers import (
    OfficerProfileSerializer,
    ParkiPayTokenObtainSerializer,
)


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Body: { "employee_id": "...", "password": "..." }
    Returns: { "access": "...", "refresh": "...", "officer": { profile } }
    All lockout logic is inside ParkiPayTokenObtainSerializer.validate().
    """

    permission_classes = [AllowAny]
    serializer_class = ParkiPayTokenObtainSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        return response


class RefreshView(TokenRefreshView):
    """
    POST /api/auth/refresh/
    Body: { "refresh": "..." }
    Returns: { "access": "...", "refresh": "..." }  (rotated)
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        return response


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Body: { "refresh": "..." }
    Blacklists the refresh token so it cannot be used again.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "refresh_required", "detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as e:
            return Response(
                {"error": "invalid_token", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        log_action(
            request.user, AuditLog.Action.LOGOUT, result="success", request=request
        )
        return Response(
            {"detail": "Logged out successfully."}, status=status.HTTP_200_OK
        )


class MeView(APIView):
    """
    GET /api/auth/me/
    Returns the authenticated officer's profile.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = OfficerProfileSerializer(request.user)
        return Response(serializer.data)
