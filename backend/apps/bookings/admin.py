from django.contrib import admin
from .models import AvailabilityBlock, Booking, BookingCancellation, MaintenanceWindow
for model in [Booking, AvailabilityBlock, BookingCancellation, MaintenanceWindow]:
    admin.site.register(model)
