from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Company, Membership

User = get_user_model()


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "legal_name",
            "registration_number",
            "country_code",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "is_active", "created_at"]


class MembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_display_name = serializers.CharField(
        source="user.display_name", read_only=True
    )

    class Meta:
        model = Membership
        fields = [
            "id",
            "user",
            "user_email",
            "user_display_name",
            "role",
            "is_active",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user_email",
            "user_display_name",
            "is_active",
            "created_at",
        ]


class MembershipCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=[Membership.Role.MANAGER])

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, attrs):
        try:
            user = User.objects.get(email__iexact=attrs["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError({
                "email": "No registered user has this email address."
            })

        if not user.is_active or getattr(user, "is_suspended", False):
            raise serializers.ValidationError({
                "email": "This user cannot be added to a company."
            })

        attrs["user"] = user
        return attrs
