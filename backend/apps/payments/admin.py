from django.contrib import admin
from .models import Payment, Refund, WebhookEvent
for model in [Payment, Refund, WebhookEvent]:
    admin.site.register(model)
