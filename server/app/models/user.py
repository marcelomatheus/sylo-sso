from mongoengine import BooleanField, EmailField, ReferenceField, StringField

from app.models.base import TimeStampedDocument


class User(TimeStampedDocument):
    tenant = ReferenceField("Tenant", required=True)
    email = EmailField(required=True)
    name = StringField(required=True, max_length=120)
    password_hash = StringField(required=True)
    role = StringField(required=True, choices=["ADMIN", "MEMBER"], default="MEMBER")
    status = StringField(required=True, choices=["INVITED", "ACTIVE", "DISABLED"], default="ACTIVE")
    email_verified = BooleanField(default=False)
    mfa_enabled = BooleanField(default=False)
    mfa_method = StringField(choices=["EMAIL", "TOTP"])
    mfa_secret = StringField()

    meta = {
        "collection": "users",
        "indexes": [
            {"fields": ["tenant", "email"], "unique": True},
            "tenant",
            "status",
            "role",
        ],
    }
