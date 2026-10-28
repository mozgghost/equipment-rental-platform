from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeOperators
from django.db import models
from django.db.models import Q
from apps.inventory.models import Equipment

class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        CONFIRMED = "confirmed", "Confirmed"
        ACTIVE = "active", "Active rental"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"
        PAYMENT_FAILED = "payment_failed", "Payment failed"
    renter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings")
    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT, related_name="bookings")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_PAYMENT, db_index=True)
    currency = models.CharField(max_length=3, default="EUR")
    quoted_rental_amount = models.DecimalField(max_digits=12, decimal_places=2)
    quoted_deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quoted_unit_rate = models.DecimalField(max_digits=12, decimal_places=2)
    quoted_billing_unit = models.CharField(max_length=8, choices=[("hour", "Hour"), ("day", "Day")])
    quoted_billable_units = models.PositiveIntegerField()
    idempotency_key = models.CharField(max_length=128)
    request_fingerprint = models.CharField(max_length=64)
    hold_expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(ends_at__gt=models.F("starts_at")), name="booking_end_after_start"),
            models.CheckConstraint(condition=Q(quoted_rental_amount__gte=0) & Q(quoted_deposit_amount__gte=0), name="booking_quote_nonnegative"),
            models.UniqueConstraint(fields=["renter", "idempotency_key"], name="uniq_booking_idempotency_key"),
        ]
        indexes = [models.Index(fields=["renter", "-created_at"]), models.Index(fields=["equipment", "status"]), models.Index(fields=["status", "hold_expires_at"])]

class MaintenanceWindow(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT, related_name="maintenance_windows")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    description = models.CharField(max_length=500)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PLANNED)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(ends_at__gt=models.F("starts_at")), name="maintenance_end_after_start")]
        indexes = [models.Index(fields=["equipment", "status", "starts_at"])]

class AvailabilityBlock(models.Model):
    """One exclusion-constrained table for both reservations and maintenance periods."""
    class Status(models.TextChoices):
        ACTIVE = "active", "Active block"
        RELEASED = "released", "Released block"
    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT, related_name="availability_blocks")
    period = DateTimeRangeField()
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.ACTIVE)
    booking = models.OneToOneField(Booking, null=True, blank=True, on_delete=models.PROTECT, related_name="availability_block")
    maintenance = models.OneToOneField(MaintenanceWindow, null=True, blank=True, on_delete=models.PROTECT, related_name="availability_block")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.CheckConstraint(condition=(Q(booking__isnull=False, maintenance__isnull=True) | Q(booking__isnull=True, maintenance__isnull=False)), name="availability_block_exactly_one_source"),
            ExclusionConstraint(name="no_overlapping_active_equipment_blocks", expressions=[("equipment", RangeOperators.EQUAL), ("period", RangeOperators.OVERLAPS)], condition=Q(status="active")),
        ]
        indexes = [models.Index(fields=["equipment", "status"])]

class BookingCancellation(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.PROTECT, related_name="cancellation")
    cancelled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reason = models.CharField(max_length=500, blank=True)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
