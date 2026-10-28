from django.conf import settings
from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=250, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=2, default="NL")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["is_active", "name"])]

    def __str__(self):
        return self.name

class Membership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        MANAGER = "manager", "Manager"
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="memberships")
    role = models.CharField(max_length=16, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "user"], name="uniq_company_member")]
        indexes = [models.Index(fields=["user", "is_active"]), models.Index(fields=["company", "role", "is_active"])]
