from mongoengine import DateTimeField, ListField, ReferenceField, StringField

from app.models.base import TimeStampedDocument


class OAuthAuthorizationCode(TimeStampedDocument):
    tenant = ReferenceField("Tenant", required=True)
    user = ReferenceField("User", required=True)
    client_app = ReferenceField("ClientApp", required=True)
    code_hash = StringField(required=True, unique=True)
    redirect_uri = StringField(required=True)
    scopes = ListField(StringField(), default=list)
    code_challenge = StringField()
    code_challenge_method = StringField(choices=["plain", "S256"])
    expires_at = DateTimeField(required=True)
    consumed_at = DateTimeField()

    meta = {
        "collection": "oauth_authorization_codes",
        "indexes": ["client_app", "tenant", "user", "expires_at"],
    }
