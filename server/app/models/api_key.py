from mongoengine import DateTimeField, ListField, ReferenceField, StringField

from app.models.base import TimeStampedDocument


class ApiKey(TimeStampedDocument):
    tenant = ReferenceField("Tenant", required=True)
    client_app = ReferenceField("ClientApp")
    name = StringField(required=True, max_length=120)
    key_prefix = StringField(required=True, max_length=20)
    key_hash = StringField(required=True, unique=True)
    scopes = ListField(StringField(), default=list)
    status = StringField(required=True, choices=["ACTIVE", "REVOKED"], default="ACTIVE")
    expires_at = DateTimeField()
    last_used_at = DateTimeField()

    meta = {
        "collection": "api_keys",
        "indexes": ["tenant", "client_app", "status", "expires_at"],
    }
