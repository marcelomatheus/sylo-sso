from __future__ import annotations

from datetime import UTC, datetime

from mongoengine import DateTimeField, Document


class TimeStampedDocument(Document):
    created_at = DateTimeField(default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = DateTimeField(default=lambda: datetime.now(UTC).replace(tzinfo=None))

    meta = {"abstract": True}

    def save(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        self.updated_at = datetime.now(UTC).replace(tzinfo=None)
        return super().save(*args, **kwargs)
