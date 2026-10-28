from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Company, Membership
from .permissions import has_company_role, is_company_owner
from .serializers import (
    CompanySerializer,
    MembershipCreateSerializer,
    MembershipSerializer,
)


def active_user_companies(user):
    return Company.objects.filter(
        is_active=True,
        memberships__user=user,
        memberships__is_active=True,
    ).distinct()


class CompanyListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        companies = active_user_companies(request.user)
        return Response(CompanySerializer(companies, many=True).data)

    def post(self, request):
        serializer = CompanySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            company = serializer.save()
            Membership.objects.create(
                company=company,
                user=request.user,
                role=Membership.Role.OWNER,
                is_active=True,
            )

        return Response(
            CompanySerializer(company).data,
            status=status.HTTP_201_CREATED,
        )


class CompanyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_company(self, request, company_id):
        company = get_object_or_404(
            active_user_companies(request.user),
            pk=company_id,
        )
        if not has_company_role(request.user, company.pk):
            raise PermissionDenied("You do not have access to this company.")
        return company

    def get(self, request, company_id):
        company = self.get_company(request, company_id)
        return Response(CompanySerializer(company).data)

    def patch(self, request, company_id):
        company = self.get_company(request, company_id)

        if not is_company_owner(request.user, company.pk):
            raise PermissionDenied("Only a company owner can edit company details.")

        serializer = CompanySerializer(
            company,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CompanyMembershipListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_company(self, request, company_id):
        company = get_object_or_404(
            active_user_companies(request.user),
            pk=company_id,
        )
        if not has_company_role(request.user, company.pk):
            raise PermissionDenied("You do not have access to this company.")
        return company

    def get(self, request, company_id):
        company = self.get_company(request, company_id)
        memberships = Membership.objects.filter(
            company=company,
            is_active=True,
        ).select_related("user").order_by("created_at")

        return Response(MembershipSerializer(memberships, many=True).data)

    def post(self, request, company_id):
        company = self.get_company(request, company_id)

        if not is_company_owner(request.user, company.pk):
            raise PermissionDenied("Only a company owner can add managers.")

        serializer = MembershipCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        try:
            with transaction.atomic():
                membership, created = Membership.objects.get_or_create(
                    company=company,
                    user=user,
                    defaults={
                        "role": Membership.Role.MANAGER,
                        "is_active": True,
                    },
                )

                if not created:
                    if membership.is_active:
                        raise ValidationError({
                            "email": "This user is already a member of the company."
                        })

                    membership.role = Membership.Role.MANAGER
                    membership.is_active = True
                    membership.save(update_fields=["role", "is_active"])

        except IntegrityError as exc:
            raise ValidationError({
                "email": "Could not add this user to the company."
            }) from exc

        return Response(
            MembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED,
        )


class CompanyMembershipDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, company_id, membership_id):
        company = get_object_or_404(
            active_user_companies(request.user),
            pk=company_id,
        )

        if not is_company_owner(request.user, company.pk):
            raise PermissionDenied("Only a company owner can remove a manager.")

        membership = get_object_or_404(
            Membership,
            pk=membership_id,
            company=company,
            is_active=True,
            role=Membership.Role.MANAGER,
        )

        membership.is_active = False
        membership.save(update_fields=["is_active"])

        return Response(status=status.HTTP_204_NO_CONTENT)
