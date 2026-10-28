from django.contrib.auth import authenticate, password_validation
from rest_framework import serializers
from .models import User

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=12, trim_whitespace=False)
    class Meta:
        model = User
        fields = ["email", "display_name", "password"]
    def validate_email(self, value):
        return value.strip().lower()
    def validate_password(self, value):
        password_validation.validate_password(value)
        return value
    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    def validate(self, attrs):
        user = authenticate(request=self.context.get("request"), username=attrs["email"].strip().lower(), password=attrs["password"])
        if user is None or user.is_suspended or not user.is_active:
            raise serializers.ValidationError("Invalid credentials")
        attrs["user"] = user
        return attrs
