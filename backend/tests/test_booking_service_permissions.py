
from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.bookings.services import (
    cancel_booking,
    create_maintenance,
)
from apps.inventory.models import Equipment, Location
from apps.organizations.models import Company, Membership


@pytest.fixture
def rental_setup(db):
    renter = User.objects.create_user(
        email="renter-permissions@example.test",
        password="Test-password-only-123",
    )
    manager = User.objects.create_user(
        email="manager-permissions@example.test",
        password="Test-password-only-123",
    )
    owner = User.objects.create_user(
        email="owner-permissions@example.test",
        password="Test-password-only-123",
    )

    company = Company.objects.create(name="Permissions Test Company")

    location = Location.objects.create(
        company=company,
        name="Main Yard",
        city="Rotterdam",
    )

    equipment = Equipment.objects.create(
        company=company,
        location=location,
        name="Permissions Test Excavator",
        slug="permissions-test-excavator",
        base_rate=Decimal("100.00"),
        billing_unit=Equipment.BillingUnit.DAY,
        deposit_amount=Decimal("0.00"),
        currency="EUR",
        status=Equipment.Status.PUBLISHED,
    )

    Membership.objects.create(
        company=company,
        user=manager,
        role=Membership.Role.MANAGER,
        is_active=True,
    )

    Membership.objects.create(
        company=company,
        user=owner,
        role=Membership.Role.OWNER,
        is_active=True,
    )

    start = timezone.now() + timedelta(days=5)

    booking = Booking.objects.create(
        renter=renter,
        equipment=equipment,
        starts_at=start,
        ends_at=start + timedelta(hours=8),
        status=Booking.Status.CONFIRMED,
        currency="EUR",
        quoted_rental_amount=Decimal("100.00"),
        quoted_deposit_amount=Decimal("0.00"),
        quoted_unit_rate=Decimal("100.00"),
        quoted_billing_unit=Equipment.BillingUnit.DAY,
        quoted_billable_units=1,
        idempotency_key="permissions-test-booking",
        request_fingerprint="b" * 64,
    )

    return {
        "renter": renter,
        "manager": manager,
        "owner": owner,
        "company": company,
        "location": location,
        "equipment": equipment,
        "booking": booking,
    }


@pytest.mark.django_db
def test_company_owner_can_cancel_booking(rental_setup):
    booking = cancel_booking(
        booking_id=rental_setup["booking"].pk,
        actor=rental_setup["owner"],
    )

    assert booking.status == Booking.Status.CANCELLED


@pytest.mark.django_db
def test_company_manager_can_cancel_booking(rental_setup):
    booking = cancel_booking(
        booking_id=rental_setup["booking"].pk,
        actor=rental_setup["manager"],
    )

    assert booking.status == Booking.Status.CANCELLED


@pytest.mark.django_db
def test_company_owner_can_create_maintenance(rental_setup):
    start = timezone.now() + timedelta(days=10)

    maintenance = create_maintenance(
        actor=rental_setup["owner"],
        equipment_id=rental_setup["equipment"].pk,
        starts_at=start,
        ends_at=start + timedelta(hours=2),
        description="Scheduled maintenance",
    )

    assert maintenance.equipment_id == rental_setup["equipment"].pk
    assert maintenance.created_by_id == rental_setup["owner"].pk


@pytest.mark.django_db
def test_equipment_rejects_location_from_another_company(rental_setup):
    other_company = Company.objects.create(name="Other Company")

    other_location = Location.objects.create(
        company=other_company,
        name="Other Yard",
        city="Utrecht",
    )

    equipment = rental_setup["equipment"]
    equipment.location = other_location

    with pytest.raises(ValidationError, match="same company"):
        equipment.full_clean()
