
"""Transactional booking operations. PostgreSQL is required for the exclusion invariant."""

import hashlib
import json
from datetime import timedelta

from django.contrib.postgres.fields.ranges import Range
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.inventory.models import Equipment
from apps.organizations.permissions import can_manage_company

from .domain.pricing import quote_rental
from .models import (
    AvailabilityBlock,
    Booking,
    BookingCancellation,
    MaintenanceWindow,
)


class BookingConflict(Exception):
    """Raised when an equipment time interval is already blocked."""


class IdempotencyConflict(Exception):
    """Raised when an idempotency key is reused for a different request."""


class BookingValidationError(Exception):
    """Raised when a booking or maintenance request is invalid."""


def _fingerprint(equipment_id, starts_at, ends_at):
    """Create a stable fingerprint for an idempotent booking request."""
    raw = json.dumps(
        {
            "equipment_id": equipment_id,
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
        },
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@transaction.atomic
def create_booking(
    *,
    renter,
    equipment_id: int,
    starts_at,
    ends_at,
    idempotency_key: str,
) -> Booking:
    """Create a booking and its availability block in one transaction."""
    if not idempotency_key or len(idempotency_key) > 128:
        raise BookingValidationError(
            "A valid Idempotency-Key header is required"
        )

    if starts_at.utcoffset() is None or ends_at.utcoffset() is None:
        raise BookingValidationError(
            "Rental timestamps must include a timezone offset"
        )

    if ends_at <= starts_at:
        raise BookingValidationError("The rental interval is invalid")

    fingerprint = _fingerprint(equipment_id, starts_at, ends_at)

    existing = Booking.objects.filter(
        renter=renter,
        idempotency_key=idempotency_key,
    ).first()

    if existing:
        if existing.request_fingerprint != fingerprint:
            raise IdempotencyConflict(
                "Idempotency key was already used with a different request"
            )
        return existing

    try:
        equipment = (
            Equipment.objects.select_for_update()
            .select_related("company", "location")
            .get(pk=equipment_id)
        )
    except Equipment.DoesNotExist as exc:
        raise BookingValidationError("Equipment not found") from exc

    if (
        equipment.status != Equipment.Status.PUBLISHED
        or not equipment.company.is_active
        or equipment.location.company_id != equipment.company_id
        or not equipment.location.is_active
    ):
        raise BookingValidationError("Equipment is not available for booking")

    now = timezone.now()
    if starts_at < now:
        raise BookingValidationError("The rental interval is invalid")

    quote = quote_rental(
        starts_at=starts_at,
        ends_at=ends_at,
        rate=equipment.base_rate,
        billing_unit=equipment.billing_unit,
        deposit=equipment.deposit_amount,
        currency=equipment.currency,
        minimum_hours=equipment.minimum_rental_hours,
    )

    try:
        # Keep the inner transaction so a database constraint violation
        # does not leave the outer transaction unusable.
        with transaction.atomic():
            booking = Booking.objects.create(
                renter=renter,
                equipment=equipment,
                starts_at=starts_at,
                ends_at=ends_at,
                status=Booking.Status.PENDING_PAYMENT,
                currency=quote.currency,
                quoted_rental_amount=quote.amount,
                quoted_deposit_amount=quote.deposit,
                quoted_unit_rate=quote.unit_rate,
                quoted_billing_unit=quote.billing_unit,
                quoted_billable_units=quote.billable_units,
                idempotency_key=idempotency_key,
                request_fingerprint=fingerprint,
                hold_expires_at=now + timedelta(minutes=15),
            )

            AvailabilityBlock.objects.create(
                equipment=equipment,
                booking=booking,
                period=Range(starts_at, ends_at, "[)"),
                status=AvailabilityBlock.Status.ACTIVE,
            )

        return booking

    except IntegrityError as exc:
        # Another request may have won the race for this idempotency key.
        existing = Booking.objects.filter(
            renter=renter,
            idempotency_key=idempotency_key,
        ).first()

        if existing:
            if existing.request_fingerprint == fingerprint:
                return existing

            raise IdempotencyConflict(
                "Idempotency key was already used with a different request"
            ) from exc

        # PostgreSQL exclusion constraints provide the final protection
        # against overlapping active reservations and maintenance windows.
        raise BookingConflict(
            "The equipment is already reserved for part of this interval"
        ) from exc


@transaction.atomic
def cancel_booking(
    *,
    booking_id: int,
    actor,
    reason: str = "",
) -> Booking:
    """Cancel an eligible booking as its renter or company manager/owner."""
    try:
        booking = (
            Booking.objects.select_for_update()
            .select_related("equipment__company")
            .get(pk=booking_id)
        )
    except Booking.DoesNotExist:
        raise

    allowed = (
        booking.renter_id == actor.pk
        or can_manage_company(actor, booking.equipment.company_id)
    )

    if not allowed:
        raise PermissionError("You cannot cancel this booking")

    if (
        booking.status
        not in {Booking.Status.PENDING_PAYMENT, Booking.Status.CONFIRMED}
        or booking.starts_at <= timezone.now()
    ):
        raise BookingValidationError(
            "This booking can no longer be cancelled"
        )

    booking.status = Booking.Status.CANCELLED
    booking.save(update_fields=["status", "updated_at"])

    AvailabilityBlock.objects.filter(
        booking=booking,
        status=AvailabilityBlock.Status.ACTIVE,
    ).update(status=AvailabilityBlock.Status.RELEASED)

    BookingCancellation.objects.create(
        booking=booking,
        cancelled_by=actor,
        reason=reason[:500],
    )

    return booking


@transaction.atomic
def create_maintenance(
    *,
    actor,
    equipment_id: int,
    starts_at,
    ends_at,
    description: str,
) -> MaintenanceWindow:
    """Schedule maintenance and block the equipment interval atomically."""
    try:
        equipment = (
            Equipment.objects.select_for_update()
            .select_related("company", "location")
            .get(pk=equipment_id)
        )
    except Equipment.DoesNotExist as exc:
        raise BookingValidationError("Equipment not found") from exc

    if not can_manage_company(actor, equipment.company_id):
        raise PermissionError("You cannot manage this equipment")

    if (
        not equipment.company.is_active
        or equipment.location.company_id != equipment.company_id
        or not equipment.location.is_active
    ):
        raise BookingValidationError(
            "Equipment and its location must belong to the same active company"
        )

    if starts_at.utcoffset() is None or ends_at.utcoffset() is None:
        raise BookingValidationError(
            "Maintenance timestamps must include a timezone offset"
        )

    if starts_at <= timezone.now() or ends_at <= starts_at:
        raise BookingValidationError("The maintenance interval is invalid")

    try:
        with transaction.atomic():
            maintenance = MaintenanceWindow.objects.create(
                equipment=equipment,
                starts_at=starts_at,
                ends_at=ends_at,
                description=description,
                created_by=actor,
            )

            AvailabilityBlock.objects.create(
                equipment=equipment,
                maintenance=maintenance,
                period=Range(starts_at, ends_at, "[)"),
                status=AvailabilityBlock.Status.ACTIVE,
            )

        return maintenance

    except IntegrityError as exc:
        raise BookingConflict(
            "Maintenance conflicts with another active booking "
            "or maintenance window"
        ) from exc
