from django.contrib import admin
from .models import AttributeDefinition, Category, Equipment, EquipmentAttributeValue, EquipmentCategory, EquipmentPhoto, EquipmentRateHistory, Location
for model in [Location, Category, AttributeDefinition, Equipment, EquipmentCategory, EquipmentAttributeValue, EquipmentPhoto, EquipmentRateHistory]:
    admin.site.register(model)
