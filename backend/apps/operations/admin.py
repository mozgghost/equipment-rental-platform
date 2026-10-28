from django.contrib import admin
from .models import Complaint, OutboxEvent, Review
for model in [Review, Complaint, OutboxEvent]:
    admin.site.register(model)
