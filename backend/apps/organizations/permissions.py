from apps.organizations.models import Membership


def has_company_role(user, company_id, roles=None):
    if (
        not getattr(user, "is_authenticated", False)
        or not getattr(user, "is_active", False)
        or getattr(user, "is_suspended", False)
    ):
        return False

    # Platform staff bypass membership checks only when no company role
    # is required. A staff account is not automatically an owner or manager.
    if getattr(user, "is_staff", False) and roles is None:
        return True

    memberships = Membership.objects.filter(
        company_id=company_id,
        user=user,
        is_active=True,
        company__is_active=True,
    )

    if roles is not None:
        memberships = memberships.filter(role__in=roles)

    return memberships.exists()


def can_manage_company(user, company_id):
    return has_company_role(
        user,
        company_id,
        roles=[Membership.Role.OWNER, Membership.Role.MANAGER],
    )


def is_company_owner(user, company_id):
    if (
        not getattr(user, "is_authenticated", False)
        or not getattr(user, "is_active", False)
        or getattr(user, "is_suspended", False)
    ):
        return False

    # Being platform staff does not make a user a company owner.
    return Membership.objects.filter(
        company_id=company_id,
        user=user,
        role=Membership.Role.OWNER,
        is_active=True,
        company__is_active=True,
    ).exists()
