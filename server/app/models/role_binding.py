from mongoengine import ListField, ReferenceField, StringField

from app.models.base import TimeStampedDocument


class RoleBinding(TimeStampedDocument):
    tenant = ReferenceField("Tenant", required=True)
    user = ReferenceField("User", required=True)
    client_app = ReferenceField("ClientApp", required=True)
    roles = ListField(StringField(), default=list)
    scopes = ListField(StringField(), default=list)
    status = StringField(required=True, choices=["ACTIVE", "DISABLED"], default="ACTIVE")

    meta = {
        "collection": "role_bindings",
        "indexes": [
            {"fields": ["tenant", "user", "client_app"], "unique": True},
        ],
    }
