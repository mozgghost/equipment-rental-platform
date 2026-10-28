from celery import shared_task
from django.db import transaction
from django.utils import timezone
from .models import AvailabilityBlock, Booking

@shared_task(bind=True, max_retries=5, default_retry_delay=30)
def expire_unpaid_booking_holds(self):
    """Expire stale unpaid holds and release their inventory blocks idempotently."""
    now = timezone.now()
    try:
        with transaction.atomic():
            stale = list(Booking.objects.select_for_update(skip_locked=True).filter(
                status=Booking.Status.PENDING_PAYMENT, hold_expires_at__lt=now
            ).values_list("id", flat=True)[:500])
            if not stale:
                return 0
            Booking.objects.filter(id__in=stale, status=Booking.Status.PENDING_PAYMENT).update(status=Booking.Status.EXPIRED, updated_at=now)
            AvailabilityBlock.objects.filter(booking_id__in=stale, status=AvailabilityBlock.Status.ACTIVE).update(status=AvailabilityBlock.Status.RELEASED)
            return len(stale)
    except Exception as exc:
        raise self.retry(exc=exc)
