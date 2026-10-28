import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Company, Membership


PASSWORD = "Test-password-only-123"


@pytest.fixture
def owner(db):
    return User.objects.create_user(
        email="owner@example.test",
        password=PASSWORD,
        display_name="Company Owner",
    )


@pytest.fixture
def manager(db):
    return User.objects.create_user(
        email="manager@example.test",
        password=PASSWORD,
        display_name="Company Manager",
    )


@pytest.fixture
def outsider(db):
    return User.objects.create_user(
        email="outsider@example.test",
        password=PASSWORD,
        display_name="Outside User",
    )


@pytest.fixture
def company_with_owner(owner):
    company = Company.objects.create(
        name="Test Rental Company",
        legal_name="Test Rental Company B.V.",
        country_code="NL",
    )
    Membership.objects.create(
        company=company,
        user=owner,
        role=Membership.Role.OWNER,
    )
    return company


@pytest.fixture
def owner_client(owner):
    client = APIClient()
    client.force_authenticate(user=owner)
    return client


@pytest.mark.django_db
def test_create_company_assigns_creator_as_owner(owner_client, owner):
    response = owner_client.post(
        "/api/companies/",
        {
            "name": "New Rental Company",
            "legal_name": "New Rental Company B.V.",
            "country_code": "NL",
        },
        format="json",
    )

    assert response.status_code == 201
    company_id = response.data["id"]
    assert response.data["name"] == "New Rental Company"
    assert Membership.objects.filter(
        company_id=company_id,
        user=owner,
        role=Membership.Role.OWNER,
        is_active=True,
    ).exists()


@pytest.mark.django_db
def test_company_list_only_returns_companies_user_belongs_to(
    owner_client, company_with_owner, outsider
):
    other_company = Company.objects.create(name="Private Other Company")
    Membership.objects.create(
        company=other_company,
        user=outsider,
        role=Membership.Role.OWNER,
    )

    response = owner_client.get("/api/companies/")

    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.data}
    assert company_with_owner.id in returned_ids
    assert other_company.id not in returned_ids


@pytest.mark.django_db
def test_outsider_cannot_read_or_edit_company(
    outsider, company_with_owner
):
    client = APIClient()
    client.force_authenticate(user=outsider)

    detail_url = f"/api/companies/{company_with_owner.id}/"

    assert client.get(detail_url).status_code == 404

    response = client.patch(
        detail_url,
        {"name": "Unauthorized Rename"},
        format="json",
    )
    assert response.status_code == 404
    company_with_owner.refresh_from_db()
    assert company_with_owner.name == "Test Rental Company"


@pytest.mark.django_db
def test_manager_can_read_but_cannot_edit_company_or_manage_members(
    manager, company_with_owner
):
    Membership.objects.create(
        company=company_with_owner,
        user=manager,
        role=Membership.Role.MANAGER,
    )
    client = APIClient()
    client.force_authenticate(user=manager)

    detail_url = f"/api/companies/{company_with_owner.id}/"
    members_url = f"/api/companies/{company_with_owner.id}/members/"

    assert client.get(detail_url).status_code == 200
    assert client.patch(
        detail_url,
        {"name": "Manager Rename"},
        format="json",
    ).status_code == 403

    assert client.get(members_url).status_code == 200
    assert client.post(
        members_url,
        {"email": "new-manager@example.test", "role": "manager"},
        format="json",
    ).status_code == 403

    company_with_owner.refresh_from_db()
    assert company_with_owner.name == "Test Rental Company"


@pytest.mark.django_db
def test_owner_can_add_and_deactivate_manager(
    owner_client, owner, company_with_owner, manager
):
    members_url = f"/api/companies/{company_with_owner.id}/members/"

    response = owner_client.post(
        members_url,
        {"email": manager.email, "role": "manager"},
        format="json",
    )
    assert response.status_code == 201
    membership_id = response.data["id"]

    membership = Membership.objects.get(pk=membership_id)
    assert membership.company_id == company_with_owner.id
    assert membership.user_id == manager.id
    assert membership.role == Membership.Role.MANAGER
    assert membership.is_active is True

    response = owner_client.delete(
        f"{members_url}{membership_id}/"
    )
    assert response.status_code == 204

    membership.refresh_from_db()
    assert membership.is_active is False


@pytest.mark.django_db
def test_owner_cannot_add_unknown_email_as_manager(
    owner_client, company_with_owner
):
    response = owner_client.post(
        f"/api/companies/{company_with_owner.id}/members/",
        {"email": "missing-user@example.test", "role": "manager"},
        format="json",
    )

    assert response.status_code == 400
    assert "email" in response.data


@pytest.mark.django_db
def test_owner_cannot_add_existing_member_twice(
    owner_client, company_with_owner, manager
):
    Membership.objects.create(
        company=company_with_owner,
        user=manager,
        role=Membership.Role.MANAGER,
    )

    response = owner_client.post(
        f"/api/companies/{company_with_owner.id}/members/",
        {"email": manager.email, "role": "manager"},
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_staff_is_not_implicitly_a_company_owner(
    company_with_owner, owner
):
    staff = User.objects.create_user(
        email="platform-staff@example.test",
        password=PASSWORD,
        is_staff=True,
    )
    client = APIClient()
    client.force_authenticate(user=staff)

    response = client.patch(
        f"/api/companies/{company_with_owner.id}/",
        {"name": "Staff Rename"},
        format="json",
    )

    assert response.status_code == 404
    company_with_owner.refresh_from_db()
    assert company_with_owner.name == "Test Rental Company"
