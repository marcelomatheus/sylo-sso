from mongoengine import DateTimeField, ListField, ReferenceField, StringField

from app.models.base import TimeStampedDocument


class EmailVerificationToken(TimeStampedDocument):
    tenant = ReferenceField("Tenant", required=True)
    user = ReferenceField("User", required=True)
    client_app = ReferenceField("ClientApp")
    token_hash = StringField(required=True, unique=True)
    redirect_uri = StringField()
    state = StringField()
    scopes = ListField(StringField(), default=list)
    expires_at = DateTimeField(required=True)
    consumed_at = DateTimeField()

    meta = {
        "collection": "email_verification_tokens",
        "indexes": ["tenant", "user", "expires_at", "consumed_at"],
    }
