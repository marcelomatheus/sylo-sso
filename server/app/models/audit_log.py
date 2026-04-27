from mongoengine import DictField, ReferenceField, StringField

from app.models.base import TimeStampedDocument


class AuditLog(TimeStampedDocument):
    tenant = ReferenceField("Tenant")
    user = ReferenceField("User")
    client_app = ReferenceField("ClientApp")
    action = StringField(required=True)
    actor_type = StringField(required=True, choices=["SYSTEM", "USER", "API_KEY"])
    status = StringField(required=True, choices=["SUCCESS", "FAILURE"])
    ip_address = StringField()
    details = DictField(default=dict)

    meta = {
        "collection": "audit_logs",
        "indexes": ["tenant", "user", "client_app", "action", "status", "created_at"],
    }
