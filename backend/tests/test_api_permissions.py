"""API access guardrails. Run these with pytest-django and PostgreSQL installed."""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.inventory.models import Equipment, Location
from apps.organizations.models import Company, Membership


@pytest.mark.django_db
def test_booking_create_requires_authenticated_user():
    client = APIClient(enforce_csrf_checks=True)
    response = client.post(
        "/api/bookings/",
        {
            "equipment_id": 1,
            "starts_at": "2026-12-01T10:00:00Z",
            "ends_at": "2026-12-01T12:00:00Z",
        },
        format="json",
    )
    assert response.status_code in {401, 403}


@pytest.mark.django_db
def test_catalog_is_public():
    response = APIClient().get("/api/catalog/equipment/")
    assert response.status_code == 200
    assert "results" in response.data


@pytest.mark.django_db
def test_inactive_company_member_cannot_read_or_cancel_company_booking():
    renter = User.objects.create_user(
        email="renter@example.test", password="Test-password-only-123"
    )
    inactive_member = User.objects.create_user(
        email="inactive-manager@example.test", password="Test-password-only-123"
    )
    company = Company.objects.create(name="Tenant Isolation Test Ltd")
    Membership.objects.create(
        company=company,
        user=inactive_member,
        role=Membership.Role.MANAGER,
        is_active=False,
    )
    location = Location.objects.create(company=company, name="Yard", city="Rotterdam")
    equipment = Equipment.objects.create(
        company=company,
        location=location,
        name="Tenant Isolation Excavator",
        slug="tenant-isolation-excavator",
        base_rate=Decimal("100.00"),
        billing_unit=Equipment.BillingUnit.DAY,
        deposit_amount=Decimal("0.00"),
        currency="EUR",
        status=Equipment.Status.PUBLISHED,
    )
    start = timezone.now() + timedelta(days=3)
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
        idempotency_key="tenant-isolation-test-booking",
        request_fingerprint="a" * 64,
    )

    client = APIClient()
    client.force_authenticate(user=inactive_member)
    assert client.get(f"/api/bookings/{booking.pk}/").status_code == 404
    assert client.post(
        f"/api/bookings/{booking.pk}/", {"reason": "not allowed"}, format="json"
    ).status_code == 404
