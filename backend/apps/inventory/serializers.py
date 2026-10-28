
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import (
    Category,
    Equipment,
    EquipmentCategory,
    EquipmentPhoto,
    EquipmentRateHistory,
    Location,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description"]


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "id",
            "name",
            "city",
            "country_code",
            "latitude",
            "longitude",
        ]


class EquipmentPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentPhoto
        fields = [
            "id",
            "object_key",
            "alt_text",
            "position",
            "is_primary",
        ]


class EquipmentSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        source="company.name",
        read_only=True,
    )
    location = LocationSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    photos = EquipmentPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Equipment
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "company_name",
            "location",
            "categories",
            "photos",
            "base_rate",
            "billing_unit",
            "minimum_rental_hours",
            "deposit_amount",
            "currency",
            "status",
        ]


class EquipmentManagementSerializer(serializers.ModelSerializer):
    location_id = serializers.PrimaryKeyRelatedField(
        source="location",
        queryset=Location.objects.filter(is_active=True),
    )
    category_ids = serializers.PrimaryKeyRelatedField(
        source="categories",
        queryset=Category.objects.filter(is_active=True),
        many=True,
        required=False,
    )

    class Meta:
        model = Equipment
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "location_id",
            "category_ids",
            "serial_number",
            "base_rate",
            "billing_unit",
            "minimum_rental_hours",
            "deposit_amount",
            "currency",
            "status",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        company = self.context["company"]
        location = attrs.get(
            "location",
            self.instance.location if self.instance else None,
        )

        if location is None or location.company_id != company.id:
            raise serializers.ValidationError({
                "location_id": "Location must belong to this company."
            })

        status_value = attrs.get(
            "status",
            self.instance.status if self.instance else Equipment.Status.DRAFT,
        )

        if (
            self.instance
            and self.instance.status == Equipment.Status.ARCHIVED
            and status_value != Equipment.Status.ARCHIVED
        ):
            raise serializers.ValidationError({
                "status": "Archived equipment cannot be reactivated."
            })

        if status_value == Equipment.Status.PUBLISHED:
            if not company.is_active or not location.is_active:
                raise serializers.ValidationError({
                    "status": (
                        "Publishing requires an active company and location."
                    )
                })

        if "currency" in attrs:
            attrs["currency"] = attrs["currency"].upper()

        return attrs

    def _save_categories(self, equipment, categories):
        if categories is None:
            return

        EquipmentCategory.objects.filter(
            equipment=equipment,
        ).exclude(
            category__in=categories,
        ).delete()

        for category in categories:
            EquipmentCategory.objects.get_or_create(
                equipment=equipment,
                category=category,
            )

    def _record_rate(self, equipment, user):
        EquipmentRateHistory.objects.create(
            equipment=equipment,
            base_rate=equipment.base_rate,
            deposit_amount=equipment.deposit_amount,
            billing_unit=equipment.billing_unit,
            effective_from=timezone.now(),
            changed_by=user,
        )

    @transaction.atomic
    def create(self, validated_data):
        categories = validated_data.pop("categories", [])
        company = self.context["company"]
        user = self.context["request"].user

        equipment = Equipment.objects.create(
            company=company,
            **validated_data,
        )
        self._save_categories(equipment, categories)
        self._record_rate(equipment, user)

        return equipment

    @transaction.atomic
    def update(self, instance, validated_data):
        categories = validated_data.pop("categories", None)
        user = self.context["request"].user

        rate_fields = {
            "base_rate",
            "deposit_amount",
            "billing_unit",
        }
        rate_changed = any(
            field in validated_data
            and validated_data[field] != getattr(instance, field)
            for field in rate_fields
        )

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if instance.status == Equipment.Status.ARCHIVED:
            instance.archived_at = (
                instance.archived_at or timezone.now()
            )
        elif "status" in validated_data:
            instance.archived_at = None

        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                raise serializers.ValidationError(
                    exc.message_dict
                ) from exc

            raise serializers.ValidationError(
                exc.messages
            ) from exc

        instance.save()

        if categories is not None:
            self._save_categories(instance, categories)

        if rate_changed:
            self._record_rate(instance, user)

        return instance
