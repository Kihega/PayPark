from django.utils import timezone
from django.db.models import Sum, Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import ControlNumber, BillStatus, get_active_bill_for_plate, generate_control_number
from vehicles.models import Vehicle, ParkingLocation
from accounts.models import log_action, AuditLog
from accounts.permissions import IsSupervisor
from notifications.tasks import send_sms_notification, send_email_notification


class GenerateBillView(APIView):
    """
    POST /api/billing/generate/
    Core endpoint — enforces the global duplicate-prevention rule.
    Only one ACTIVE control number may exist per plate at any time,
    across ALL officers and ALL locations.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plate = request.data.get("plate_number", "").strip().upper()
        location_id = request.data.get("location_id")

        if not plate:
            return Response(
                {"error": "plate_required", "detail": "Plate number is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── GLOBAL DUPLICATE CHECK ────────────────────────────────────────────
        active_bill = get_active_bill_for_plate(plate)
        if active_bill:
            log_action(
                request.user,
                AuditLog.Action.BILL_DUPLICATE_BLOCKED,
                plate_number=plate,
                control_number=active_bill.control_number,
                result="duplicate_blocked",
                request=request,
            )
            return Response(
                {
                    "error": "active_bill_exists",
                    "detail": (
                        "An active bill already exists for this vehicle. "
                        "No new bill can be generated until it expires."
                    ),
                    "existing_bill": {
                        "control_number": active_bill.control_number,
                        "issued_by": active_bill.officer.full_name if active_bill.officer else "Unknown",
                        "issued_by_id": active_bill.officer.employee_id if active_bill.officer else None,
                        "location": active_bill.location.name if active_bill.location else "Unknown",
                        "generated_at": active_bill.generated_at,
                        "expires_at": active_bill.expires_at,
                        "amount_due": str(active_bill.amount_due),
                    },
                },
                status=status.HTTP_409_CONFLICT,
            )

        # ── VEHICLE LOOKUP ────────────────────────────────────────────────────
        try:
            vehicle = Vehicle.objects.get(plate_number__iexact=plate)
        except Vehicle.DoesNotExist:
            return Response(
                {"error": "plate_not_found", "detail": "Vehicle not found in registry."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ── LOCATION ──────────────────────────────────────────────────────────
        location = None
        if location_id:
            try:
                location = ParkingLocation.objects.get(id=location_id, is_active=True)
            except ParkingLocation.DoesNotExist:
                return Response(
                    {"error": "invalid_location", "detail": "Location not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif request.user.location:
            location = request.user.location

        # ── FEE CALCULATION ───────────────────────────────────────────────────
        amount = location.get_fee_for_category(vehicle.category) if location else 2000

        # ── CREATE BILL ───────────────────────────────────────────────────────
        bill = ControlNumber.objects.create(
            plate_number=vehicle.plate_number,
            vehicle=vehicle,
            officer=request.user,
            location=location,
            amount_due=amount,
        )

        log_action(
            request.user,
            AuditLog.Action.BILL_GENERATED,
            plate_number=vehicle.plate_number,
            control_number=bill.control_number,
            result="success",
            request=request,
        )

        # ── DISPATCH NOTIFICATIONS (async) ────────────────────────────────────
        send_sms_notification.delay(bill.id)
        if vehicle.owner_email:
            send_email_notification.delay(bill.id)

        return Response(
            {
                "control_number": bill.control_number,
                "plate_number": bill.plate_number,
                "owner_name": vehicle.owner_name,
                "owner_phone": vehicle.owner_phone,
                "amount_due": str(bill.amount_due),
                "generated_at": bill.generated_at,
                "expires_at": bill.expires_at,
                "location": location.name if location else None,
                "sms_sent": bill.sms_sent,
            },
            status=status.HTTP_201_CREATED,
        )


class BillStatusView(APIView):
    """GET /api/billing/{control_number}/status/ — poll for SMS/email status."""
    permission_classes = [IsAuthenticated]

    def get(self, request, control_number):
        try:
            bill = ControlNumber.objects.get(control_number=control_number)
        except ControlNumber.DoesNotExist:
            return Response({"error": "not_found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "control_number": bill.control_number,
            "status": bill.status,
            "sms_sent": bill.sms_sent,
            "email_sent": bill.email_sent,
            "expires_at": bill.expires_at,
        })


class BillingHistoryView(APIView):
    """GET /api/billing/history/?date=YYYY-MM-DD — officer's daily bill history."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.utils.dateparse import parse_date
        date_str = request.query_params.get("date")
        if date_str:
            target_date = parse_date(date_str)
        else:
            target_date = timezone.localdate()

        bills = ControlNumber.objects.filter(
            officer=request.user,
            generated_at__date=target_date,
        ).select_related("location").order_by("-generated_at")

        data = [
            {
                "id": b.id,
                "control_number": b.control_number,
                "plate_number": b.plate_number,
                "amount_due": str(b.amount_due),
                "location": b.location.name if b.location else None,
                "generated_at": b.generated_at,
                "expires_at": b.expires_at,
                "status": b.status,
                "sms_sent": b.sms_sent,
            }
            for b in bills
        ]

        return Response({"date": str(target_date), "bills": data, "total": len(data)})


class DailySummaryView(APIView):
    """GET /api/billing/daily-summary/ — stats for officer's current day."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        qs = ControlNumber.objects.filter(officer=request.user, generated_at__date=today)
        stats = qs.aggregate(
            total_bills=Count("id"),
            total_amount=Sum("amount_due"),
            active_bills=Count("id", filter=Q(status=BillStatus.ACTIVE)),
            expired_bills=Count("id", filter=Q(status=BillStatus.EXPIRED)),
        )
        return Response({
            "date": str(today),
            "total_bills": stats["total_bills"] or 0,
            "total_amount": str(stats["total_amount"] or 0),
            "active_bills": stats["active_bills"] or 0,
            "expired_bills": stats["expired_bills"] or 0,
        })
