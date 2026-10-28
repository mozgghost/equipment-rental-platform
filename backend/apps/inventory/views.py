from decimal import Decimal, InvalidOperation

from django.contrib.postgres.fields.ranges import Range
from django.utils.dateparse import parse_datetime
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Category, Equipment
from .serializers import CategorySerializer, EquipmentSerializer


def _price_param(params, name):
    raw = params.get(name)
    if raw in (None, ""):
        return None
    try:
        value = Decimal(raw)
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError({name: "Must be a valid decimal amount."}) from None
    if not value.is_finite() or value < 0:
        raise ValidationError({name: "Must be a finite, non-negative amount."})
    return value


class CategoryListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    pagination_class = None


class EquipmentListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    serializer_class = EquipmentSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["location__city", "location__country_code", "billing_unit"]
    search_fields = ["name", "description", "company__name", "location__city"]
    ordering_fields = ["base_rate", "name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        qs = Equipment.objects.filter(
            status=Equipment.Status.PUBLISHED, company__is_active=True, location__is_active=True
        ).select_related("company", "location").prefetch_related("categories", "photos")
        params = self.request.query_params
        category_slug = params.get("category")
        if category_slug:
            qs = qs.filter(categories__slug=category_slug)

        min_price = _price_param(params, "min_price")
        max_price = _price_param(params, "max_price")
        if min_price is not None and max_price is not None and min_price > max_price:
            raise ValidationError({"max_price": "Must be greater than or equal to min_price."})
        if min_price is not None:
            qs = qs.filter(base_rate__gte=min_price)
        if max_price is not None:
            qs = qs.filter(base_rate__lte=max_price)

        start_raw, end_raw = params.get("available_from"), params.get("available_to")
        if start_raw or end_raw:
            start, end = parse_datetime(start_raw or ""), parse_datetime(end_raw or "")
            if (not start or not end or start.utcoffset() is None or end.utcoffset() is None
                    or end <= start):
                raise ValidationError({
                    "availability": "Provide timezone-aware available_from and available_to; end must be after start."
                })
            qs = qs.exclude(
                availability_blocks__status="active",
                availability_blocks__period__overlap=Range(start, end, "[)"),
            )
        return qs.distinct()


class EquipmentDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    serializer_class = EquipmentSerializer
    lookup_field = "slug"
    queryset = Equipment.objects.filter(
        status=Equipment.Status.PUBLISHED, company__is_active=True, location__is_active=True
    ).select_related("company", "location").prefetch_related("categories", "photos")
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from apps.organizations.models import Company
from apps.organizations.permissions import can_manage_company

from .serializers import EquipmentManagementSerializer


class CompanyEquipmentListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EquipmentManagementSerializer

    def get_company(self):
        company = get_object_or_404(
            Company,
            pk=self.kwargs["company_id"],
            is_active=True,
        )
        if not can_manage_company(self.request.user, company.pk):
            raise PermissionDenied(
                "You cannot manage equipment for this company."
            )
        return company

    def get_queryset(self):
        return (
            Equipment.objects.filter(company=self.get_company())
            .select_related("company", "location")
            .prefetch_related("categories", "photos")
            .order_by("name")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["company"] = self.get_company()
        return context


class CompanyEquipmentDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EquipmentManagementSerializer
    lookup_url_kwarg = "equipment_id"
    http_method_names = ["get", "put", "patch", "head", "options"]

    def get_company(self):
        company = get_object_or_404(
            Company,
            pk=self.kwargs["company_id"],
            is_active=True,
        )
        if not can_manage_company(self.request.user, company.pk):
            raise PermissionDenied(
                "You cannot manage equipment for this company."
            )
        return company

    def get_queryset(self):
        return (
            Equipment.objects.filter(company=self.get_company())
            .select_related("company", "location")
            .prefetch_related("categories", "photos")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["company"] = self.get_company()
        return context
