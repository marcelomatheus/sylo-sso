from mongoengine import DateTimeField, ReferenceField, StringField

from app.models.base import TimeStampedDocument


class MfaChallenge(TimeStampedDocument):
    tenant = ReferenceField("Tenant", required=True)
    user = ReferenceField("User", required=True)
    code_hash = StringField(required=True, unique=True)
    method = StringField(required=True, choices=["EMAIL", "TOTP"])
    expires_at = DateTimeField(required=True)
    consumed_at = DateTimeField()

    meta = {
        "collection": "mfa_challenges",
        "indexes": ["tenant", "user", "method", "expires_at", "consumed_at"],
    }
