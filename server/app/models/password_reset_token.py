from mongoengine import DateTimeField, ReferenceField, StringField

from app.models.base import TimeStampedDocument


class PasswordResetToken(TimeStampedDocument):
    tenant = ReferenceField("Tenant", required=True)
    user = ReferenceField("User", required=True)
    token_hash = StringField(required=True, unique=True)
    expires_at = DateTimeField(required=True)
    consumed_at = DateTimeField()

    meta = {
        "collection": "password_reset_tokens",
        "indexes": ["tenant", "user", "expires_at", "consumed_at"],
    }
