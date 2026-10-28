from django.utils.dateparse import parse_datetime
from rest_framework import serializers

from .models import Booking


class AwareDateTimeField(serializers.DateTimeField):
    """Reject ambiguous timestamps instead of silently assuming the server timezone."""

    default_error_messages = {
        "timezone_required": "Provide an ISO-8601 timestamp with a timezone offset, for example 2026-12-01T10:00:00Z."
    }

    def to_internal_value(self, value):
        if isinstance(value, str):
            parsed = parse_datetime(value)
            if parsed is None or parsed.utcoffset() is None:
                self.fail("timezone_required")
        elif hasattr(value, "utcoffset") and value.utcoffset() is None:
            self.fail("timezone_required")
        return super().to_internal_value(value)


class BookingCreateSerializer(serializers.Serializer):
    equipment_id = serializers.IntegerField(min_value=1)
    starts_at = AwareDateTimeField()
    ends_at = AwareDateTimeField()

    def validate(self, attrs):
        if attrs["ends_at"] <= attrs["starts_at"]:
            raise serializers.ValidationError({"ends_at": "Must be after starts_at."})
        return attrs


class BookingSerializer(serializers.ModelSerializer):
    equipment_name = serializers.CharField(source="equipment.name", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id", "equipment", "equipment_name", "starts_at", "ends_at", "status",
            "currency", "quoted_rental_amount", "quoted_deposit_amount", "quoted_unit_rate",
            "quoted_billing_unit", "quoted_billable_units", "hold_expires_at", "created_at",
        ]
        read_only_fields = fields
