from datetime import UTC, datetime, timedelta

from mongoengine import DateTimeField, DictField, ReferenceField, StringField

from app.core.config import get_settings
from app.models.base import TimeStampedDocument


class TelemetryLog(TimeStampedDocument):
    tenant = ReferenceField("Tenant")
    user = ReferenceField("User")
    client_app = ReferenceField("ClientApp")
    event_type = StringField(required=True)
    metadata = DictField(default=dict)
    expires_at = DateTimeField(default=lambda: datetime.now(UTC).replace(tzinfo=None))

    meta = {
        "collection": "telemetry_logs",
        "indexes": [
            "tenant",
            "event_type",
            "created_at",
            {"fields": ["expires_at"], "expireAfterSeconds": 0},
        ],
    }

    def save(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        settings = get_settings()
        base_time = self.created_at or datetime.now(UTC).replace(tzinfo=None)
        if self.expires_at <= base_time:
            self.expires_at = base_time + timedelta(seconds=settings.telemetry_ttl_seconds)
        return super().save(*args, **kwargs)
