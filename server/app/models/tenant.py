from mongoengine import BooleanField, EmbeddedDocument, EmbeddedDocumentField, EmailField, StringField

from app.models.base import TimeStampedDocument


class BrandingSettings(EmbeddedDocument):
    logo_url = StringField()
    primary_color = StringField(default="#f97316")
    secondary_color = StringField(default="#111827")
    font_family = StringField(default="Space Grotesk")
    support_email = EmailField()
    login_title = StringField(default="Acesse sua conta")
    login_subtitle = StringField(default="Autenticacao centralizada para seus aplicativos.")


class Tenant(TimeStampedDocument):
    name = StringField(required=True, max_length=120)
    slug = StringField(required=True, unique=True, max_length=80)
    contact_email = EmailField(required=True)
    plan = StringField(default="starter", choices=["starter", "growth", "enterprise"])
    status = StringField(default="ACTIVE", choices=["ACTIVE", "SUSPENDED"])
    branding = EmbeddedDocumentField(BrandingSettings, default=BrandingSettings)
    lgpd_consent_required = BooleanField(default=True)

    meta = {
        "collection": "tenants",
        "indexes": ["slug", "status"],
    }
