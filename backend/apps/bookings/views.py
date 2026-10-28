from django.db.models import Q
from django.http import Http404
from rest_framework import permissions, status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.organizations.models import Membership
from .serializers import BookingCreateSerializer, BookingSerializer
from .services import BookingConflict, BookingValidationError, IdempotencyConflict, cancel_booking, create_booking
from .models import Booking

class ConflictResponse(APIException):
    status_code = 409
    default_detail = "Booking conflict"
    default_code = "booking_conflict"

def accessible_bookings(user):
    qs = Booking.objects.select_related("equipment", "equipment__company")
    if user.is_staff:
        return qs
    return qs.filter(
        Q(renter=user)
        | Q(equipment__company__memberships__user=user, equipment__company__memberships__is_active=True)
    )

class BookingListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        qs = accessible_bookings(request.user).distinct().order_by("-created_at")
        # MVP page cap; use standard DRF pagination when this becomes a ViewSet.
        return Response(BookingSerializer(qs[:100], many=True).data)
    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            booking = create_booking(renter=request.user, **serializer.validated_data, idempotency_key=request.headers.get("Idempotency-Key", ""))
        except (BookingConflict, IdempotencyConflict) as exc:
            raise ConflictResponse(str(exc)) from exc
        except BookingValidationError as exc:
            raise ValidationError({"booking": str(exc)}) from exc
        except Exception as exc:
            from django.core.exceptions import ObjectDoesNotExist
            if isinstance(exc, ObjectDoesNotExist):
                raise ValidationError({"equipment_id": "Equipment not found"}) from exc
            raise
        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)

class BookingDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get_object(self, request, booking_id):
        try:
            return accessible_bookings(request.user).distinct().get(pk=booking_id)
        except Booking.DoesNotExist as exc:
            raise Http404 from exc
    def get(self, request, booking_id):
        return Response(BookingSerializer(self.get_object(request, booking_id)).data)
    def post(self, request, booking_id):
        # Hide existence for resources outside the caller's access scope before invoking the domain service.
        self.get_object(request, booking_id)
        reason = str(request.data.get("reason", ""))[:500]
        try:
            booking = cancel_booking(booking_id=booking_id, actor=request.user, reason=reason)
        except (BookingConflict, IdempotencyConflict) as exc:
            raise ConflictResponse(str(exc)) from exc
        except BookingValidationError as exc:
            raise ValidationError({"booking": str(exc)}) from exc
        except PermissionError as exc:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(str(exc)) from exc
        except Booking.DoesNotExist as exc:
            raise Http404 from exc
        return Response(BookingSerializer(booking).data)
