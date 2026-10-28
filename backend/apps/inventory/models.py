from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.core.exceptions import ValidationError
from apps.organizations.models import Company

class Location(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="locations")
    name = models.CharField(max_length=160)
    address_line = models.CharField(max_length=250, blank=True)
    city = models.CharField(max_length=120, db_index=True)
    postal_code = models.CharField(max_length=24, blank=True)
    country_code = models.CharField(max_length=2, default="NL")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=(models.Q(latitude__isnull=True, longitude__isnull=True) | models.Q(latitude__isnull=False, longitude__isnull=False)), name="location_coordinates_pair")]
        indexes = [models.Index(fields=["country_code", "city", "is_active"])]

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    class Meta:
        ordering = ["sort_order", "name"]

class AttributeDefinition(models.Model):
    class ValueType(models.TextChoices):
        TEXT = "text", "Text"
        NUMBER = "number", "Number"
        BOOLEAN = "boolean", "Boolean"
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    unit = models.CharField(max_length=32, blank=True)
    value_type = models.CharField(max_length=12, choices=ValueType.choices)
    filterable = models.BooleanField(default=True)
    class Meta:
        ordering = ["name"]

class Equipment(models.Model):
    def clean(self):
        super().clean()
        if (
            self.company_id
            and self.location_id
            and self.location.company_id != self.company_id
        ):
            raise ValidationError({
                "location": "Location must belong to the same company as equipment."
            })
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        PAUSED = "paused", "Paused"
        ARCHIVED = "archived", "Archived"
    class BillingUnit(models.TextChoices):
        HOUR = "hour", "Hour"
        DAY = "day", "Day"
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="equipment")
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="equipment")
    name = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True)
    description = models.TextField(blank=True)
    serial_number = models.CharField(max_length=120, blank=True)
    categories = models.ManyToManyField(Category, through="EquipmentCategory", related_name="equipment")
    base_rate = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    billing_unit = models.CharField(max_length=8, choices=BillingUnit.choices, default=BillingUnit.DAY)
    minimum_rental_hours = models.PositiveSmallIntegerField(default=1)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default="EUR")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(base_rate__gte=0), name="equipment_rate_nonnegative"), models.CheckConstraint(condition=models.Q(deposit_amount__gte=0), name="equipment_deposit_nonnegative"), models.CheckConstraint(condition=models.Q(minimum_rental_hours__gte=1), name="equipment_min_duration_positive")]
        indexes = [models.Index(fields=["status", "created_at"]), models.Index(fields=["location", "status"]), models.Index(fields=["company", "status"]), models.Index(fields=["name"])]

class EquipmentCategory(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["equipment", "category"], name="uniq_equipment_category")]

class EquipmentAttributeValue(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name="attribute_values")
    attribute = models.ForeignKey(AttributeDefinition, on_delete=models.PROTECT, related_name="values")
    text_value = models.CharField(max_length=400, blank=True)
    number_value = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    boolean_value = models.BooleanField(null=True, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["equipment", "attribute"], name="uniq_equipment_attribute_value")]
        indexes = [models.Index(fields=["attribute", "number_value"]), models.Index(fields=["attribute", "boolean_value"])]

class EquipmentPhoto(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name="photos")
    object_key = models.CharField(max_length=500)
    alt_text = models.CharField(max_length=250, blank=True)
    position = models.PositiveSmallIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["position", "id"]
        constraints = [models.UniqueConstraint(fields=["equipment"], condition=models.Q(is_primary=True), name="uniq_primary_equipment_photo")]

class EquipmentRateHistory(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT, related_name="rate_history")
    base_rate = models.DecimalField(max_digits=12, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    billing_unit = models.CharField(max_length=8, choices=Equipment.BillingUnit.choices)
    effective_from = models.DateTimeField()
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-effective_from"]
        indexes = [models.Index(fields=["equipment", "effective_from"])]
