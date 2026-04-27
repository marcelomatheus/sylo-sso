from mongoengine import DateTimeField, ListField, ReferenceField, StringField

from app.models.base import TimeStampedDocument


class AuthSession(TimeStampedDocument):
    tenant = ReferenceField("Tenant", required=True)
    user = ReferenceField("User", required=True)
    client_app = ReferenceField("ClientApp")
    refresh_token_hash = StringField(required=True, unique=True)
    scopes = ListField(StringField(), default=list)
    access_token_jti = StringField()
    expires_at = DateTimeField(required=True)
    revoked_at = DateTimeField()

    meta = {
        "collection": "auth_sessions",
        "indexes": ["tenant", "user", "expires_at", "revoked_at"],
    }
