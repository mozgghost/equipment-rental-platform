from django.conf import settings
from django.db import models
from apps.bookings.models import Booking

class Payment(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        REQUIRES_ACTION = "requires_action", "Requires action"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"
        PARTIALLY_REFUNDED = "partially_refunded", "Partially refunded"
    class Purpose(models.TextChoices):
        RENTAL = "rental", "Rental charge"
        DEPOSIT = "deposit", "Deposit"
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT, related_name="payments")
    purpose = models.CharField(max_length=12, choices=Purpose.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.CREATED, db_index=True)
    provider = models.CharField(max_length=40, blank=True)
    provider_payment_id = models.CharField(max_length=180, blank=True)
    idempotency_key = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(amount__gte=0), name="payment_amount_nonnegative")]
        indexes = [models.Index(fields=["booking", "status"])]

class Refund(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refunds")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.REQUESTED)
    provider_refund_id = models.CharField(max_length=180, blank=True)
    idempotency_key = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(amount__gt=0), name="refund_amount_positive")]

class WebhookEvent(models.Model):
    provider = models.CharField(max_length=40)
    provider_event_id = models.CharField(max_length=180)
    event_type = models.CharField(max_length=160)
    payload_digest = models.CharField(max_length=64)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.CharField(max_length=300, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["provider", "provider_event_id"], name="uniq_provider_webhook_event")]
        indexes = [models.Index(fields=["processed_at", "received_at"])]
