
import pytest
from decimal import Decimal
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.inventory.models import (
    Category,
    Equipment,
    EquipmentRateHistory,
    Location,
)
from apps.organizations.models import Company, Membership


PASSWORD = "Test-password-only-123"


@pytest.fixture
def inventory_setup(db):
    owner = User.objects.create_user(
        email="inventory-owner@example.test",
        password=PASSWORD,
        display_name="Inventory Owner",
    )
    company = Company.objects.create(name="Inventory Company")
    Membership.objects.create(
        company=company,
        user=owner,
        role=Membership.Role.OWNER,
    )
    location = Location.objects.create(
        company=company,
        name="Main Depot",
        city="Rotterdam",
        country_code="NL",
    )
    category = Category.objects.create(
        name="Excavators",
        slug="excavators",
    )

    client = APIClient()
    client.force_authenticate(user=owner)

    return {
        "owner": owner,
        "company": company,
        "location": location,
        "category": category,
        "client": client,
    }


def equipment_url(company_id):
    return f"/api/catalog/manage/companies/{company_id}/equipment/"


def valid_equipment_payload(location, category):
    return {
        "name": "Mini Excavator",
        "slug": "mini-excavator-test",
        "description": "Compact excavator for small sites",
        "location_id": location.id,
        "category_ids": [category.id],
        "serial_number": "EX-100",
        "base_rate": "85.00",
        "billing_unit": "day",
        "minimum_rental_hours": 1,
        "deposit_amount": "150.00",
        "currency": "eur",
        "status": "draft",
    }


@pytest.mark.django_db
def test_owner_can_create_equipment(inventory_setup):
    data = inventory_setup
    response = data["client"].post(
        equipment_url(data["company"].id),
        valid_equipment_payload(data["location"], data["category"]),
        format="json",
    )

    assert response.status_code == 201, response.data

    equipment = Equipment.objects.get(pk=response.data["id"])
    assert equipment.company_id == data["company"].id
    assert equipment.location_id == data["location"].id
    assert equipment.categories.filter(
        pk=data["category"].id
    ).exists()
    assert equipment.currency == "EUR"

    assert EquipmentRateHistory.objects.filter(
        equipment=equipment,
        base_rate=Decimal("85.00"),
        deposit_amount=Decimal("150.00"),
        billing_unit="day",
    ).exists()


@pytest.mark.django_db
def test_equipment_cannot_use_another_company_location(inventory_setup):
    data = inventory_setup
    other_company = Company.objects.create(name="Other Company")
    other_location = Location.objects.create(
        company=other_company,
        name="Other Depot",
        city="Utrecht",
        country_code="NL",
    )

    payload = valid_equipment_payload(
        data["location"],
        data["category"],
    )
    payload["location_id"] = other_location.id

    response = data["client"].post(
        equipment_url(data["company"].id),
        payload,
        format="json",
    )

    assert response.status_code == 400, response.data
    assert not Equipment.objects.filter(slug=payload["slug"]).exists()


@pytest.mark.django_db
def test_outsider_cannot_list_or_read_company_equipment(inventory_setup):
    data = inventory_setup
    equipment = Equipment.objects.create(
        company=data["company"],
        location=data["location"],
        name="Private Excavator",
        slug="private-excavator-test",
        base_rate=Decimal("80.00"),
    )
    outsider = User.objects.create_user(
        email="inventory-outsider@example.test",
        password=PASSWORD,
    )

    client = APIClient()
    client.force_authenticate(user=outsider)

    response_list = client.get(equipment_url(data["company"].id))
    response_detail = client.get(
        f"{equipment_url(data['company'].id)}{equipment.id}/"
    )

    assert response_list.status_code == 403
    assert response_detail.status_code == 403


@pytest.mark.django_db
def test_rate_change_creates_history(inventory_setup):
    data = inventory_setup
    equipment = Equipment.objects.create(
        company=data["company"],
        location=data["location"],
        name="Rate Test Excavator",
        slug="rate-test-excavator",
        base_rate=Decimal("80.00"),
        deposit_amount=Decimal("100.00"),
    )
    url = f"{equipment_url(data['company'].id)}{equipment.id}/"

    response = data["client"].patch(
        url,
        {"base_rate": "95.00"},
        format="json",
    )

    assert response.status_code == 200, response.data

    equipment.refresh_from_db()
    assert equipment.base_rate == Decimal("95.00")

    assert EquipmentRateHistory.objects.filter(
        equipment=equipment,
        base_rate=Decimal("95.00"),
        deposit_amount=Decimal("100.00"),
        billing_unit="day",
    ).exists()


@pytest.mark.django_db
def test_inactive_category_cannot_be_assigned(inventory_setup):
    data = inventory_setup
    inactive_category = Category.objects.create(
        name="Inactive Category",
        slug="inactive-category",
        is_active=False,
    )
    payload = valid_equipment_payload(
        data["location"],
        data["category"],
    )
    payload["category_ids"] = [inactive_category.id]

    response = data["client"].post(
        equipment_url(data["company"].id),
        payload,
        format="json",
    )

    assert response.status_code == 400, response.data
    assert not Equipment.objects.filter(slug=payload["slug"]).exists()


@pytest.mark.django_db
def test_archived_equipment_cannot_be_republished(inventory_setup):
    data = inventory_setup
    equipment = Equipment.objects.create(
        company=data["company"],
        location=data["location"],
        name="Archived Excavator",
        slug="archived-excavator-test",
        base_rate=Decimal("80.00"),
        status=Equipment.Status.ARCHIVED,
    )
    url = f"{equipment_url(data['company'].id)}{equipment.id}/"

    response = data["client"].patch(
        url,
        {"status": Equipment.Status.PUBLISHED},
        format="json",
    )

    assert response.status_code == 400, response.data

    equipment.refresh_from_db()
    assert equipment.status == Equipment.Status.ARCHIVED


@pytest.mark.django_db
def test_platform_staff_without_membership_cannot_manage_equipment(
    inventory_setup,
):
    data = inventory_setup
    staff_user = User.objects.create_user(
        email="platform-staff@example.test",
        password=PASSWORD,
        is_staff=True,
    )

    client = APIClient()
    client.force_authenticate(user=staff_user)

    response = client.get(equipment_url(data["company"].id))

    assert response.status_code == 403
