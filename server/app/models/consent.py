from mongoengine import DateTimeField, ListField, ReferenceField

from app.models.base import TimeStampedDocument


class Consent(TimeStampedDocument):
    tenant = ReferenceField("Tenant", required=True)
    user = ReferenceField("User", required=True)
    client_app = ReferenceField("ClientApp", required=True)
    scopes = ListField(required=True)
    granted_at = DateTimeField(required=True)
    revoked_at = DateTimeField()

    meta = {
        "collection": "consents",
        "indexes": [
            {"fields": ["tenant", "user", "client_app"], "unique": True},
        ],
    }
