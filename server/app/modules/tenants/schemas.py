from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TenantBrandingPayload(BaseModel):
    logo_url: str | None = None
    primary_color: str = Field(default="#f97316", pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: str = Field(default="#111827", pattern=r"^#[0-9A-Fa-f]{6}$")
    font_family: str = Field(default="Space Grotesk", min_length=2, max_length=80)
    support_email: EmailStr | None = None
    login_title: str = Field(default="Acesse sua conta", min_length=4, max_length=120)
    login_subtitle: str = Field(default="Autenticacao centralizada para seus aplicativos.", min_length=8, max_length=180)


class TenantCreateSchema(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    slug: str = Field(min_length=3, max_length=80, pattern=r"^[a-z0-9-]+$")
    contact_email: EmailStr
    plan: str = Field(default="starter", pattern="^(starter|growth|enterprise)$")
    branding: TenantBrandingPayload | None = None
    lgpd_consent_required: bool = True


class BootstrapSchema(BaseModel):
    tenant: TenantCreateSchema
    admin_name: str = Field(min_length=3, max_length=120)
    admin_email: EmailStr
    admin_password: str = Field(min_length=8, max_length=128)


class TenantUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=120)
    contact_email: EmailStr | None = None
    plan: str | None = Field(default=None, pattern="^(starter|growth|enterprise)$")
    status: str | None = Field(default=None, pattern="^(ACTIVE|SUSPENDED)$")
    branding: TenantBrandingPayload | None = None
    lgpd_consent_required: bool | None = None


class TenantResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    contact_email: EmailStr
    plan: str
    status: str
    lgpd_consent_required: bool
    branding: TenantBrandingPayload
    created_at: datetime
    updated_at: datetime


class TenantPathSchema(BaseModel):
    tenant_id: str


class TenantSlugPathSchema(BaseModel):
    tenant_slug: str


class WhiteLabelResponseSchema(BaseModel):
    tenant_name: str
    tenant_slug: str
    branding: TenantBrandingPayload
    lgpd_consent_required: bool
