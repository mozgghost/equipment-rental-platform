from django.conf import settings
from django.db import models

class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=120, db_index=True)
    object_type = models.CharField(max_length=120)
    object_id = models.CharField(max_length=100, blank=True)
    request_id = models.CharField(max_length=80, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    class Meta:
        indexes = [models.Index(fields=["object_type", "object_id", "-created_at"]), models.Index(fields=["actor", "-created_at"])]
