"""PostgreSQL-only integration tests for allocation invariants.

These tests are intentionally not considered proven until they pass against the target PostgreSQL major version.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier

import pytest
from django.db import close_old_connections, connection
from django.utils import timezone

from apps.accounts.models import User
from apps.bookings.models import AvailabilityBlock, Booking
from apps.bookings.services import BookingConflict, create_booking
from apps.inventory.models import Equipment, Location
from apps.organizations.models import Company

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(connection.vendor != "postgresql", reason="Requires PostgreSQL exclusion constraints")]

@pytest.fixture
def listing(db):
    owner = User.objects.create_user(email="supplier@example.test", password="Test-password-only-123")
    company = Company.objects.create(name="Test Equipment Ltd")
    location = Location.objects.create(company=company, name="Main yard", city="Rotterdam")
    equipment = Equipment.objects.create(company=company, location=location, name="Test excavator", slug="test-excavator",
        base_rate=Decimal("100.00"), billing_unit=Equipment.BillingUnit.DAY, minimum_rental_hours=1,
        deposit_amount=Decimal("200.00"), currency="EUR", status=Equipment.Status.PUBLISHED)
    renters = [User.objects.create_user(email=f"renter{i}@example.test", password="Test-password-only-123") for i in range(2)]
    return equipment, renters

def test_overlapping_concurrent_booking_attempts_only_allow_one(listing):
    equipment, renters = listing
    start = timezone.now() + timedelta(days=2)
    barrier = Barrier(2)
    def attempt(user):
        close_old_connections()
        try:
            barrier.wait(timeout=5)
            try:
                result = create_booking(renter=user, equipment_id=equipment.id, starts_at=start,
                    ends_at=start + timedelta(hours=8), idempotency_key=f"parallel-{user.id}")
                return ("created", result.pk)
            except BookingConflict:
                return ("conflict", None)
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, renters))
    assert sorted(x[0] for x in results) == ["conflict", "created"]
    assert AvailabilityBlock.objects.filter(equipment=equipment, status=AvailabilityBlock.Status.ACTIVE).count() == 1
    assert Booking.objects.filter(equipment=equipment, status=Booking.Status.PENDING_PAYMENT).count() == 1

def test_adjacent_half_open_intervals_are_both_allowed(listing):
    equipment, renters = listing
    start = timezone.now() + timedelta(days=4)
    first = create_booking(renter=renters[0], equipment_id=equipment.id, starts_at=start,
        ends_at=start + timedelta(hours=8), idempotency_key="adjacent-a")
    second = create_booking(renter=renters[1], equipment_id=equipment.id, starts_at=first.ends_at,
        ends_at=first.ends_at + timedelta(hours=8), idempotency_key="adjacent-b")
    assert first.pk != second.pk
    assert AvailabilityBlock.objects.filter(equipment=equipment, status=AvailabilityBlock.Status.ACTIVE).count() == 2
