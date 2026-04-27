from mongoengine import BooleanField, ListField, ReferenceField, StringField

from app.models.base import TimeStampedDocument


class ClientApp(TimeStampedDocument):
    tenant = ReferenceField("Tenant", required=True)
    name = StringField(required=True, max_length=120)
    description = StringField()
    client_id = StringField(required=True, unique=True)
    client_secret_hash = StringField()
    is_public = BooleanField(default=False)
    redirect_uris = ListField(StringField(), default=list)
    allowed_scopes = ListField(StringField(), default=list)
    status = StringField(required=True, choices=["ACTIVE", "DISABLED"], default="ACTIVE")

    meta = {
        "collection": "client_apps",
        "indexes": ["tenant", "client_id", "status"],
    }
