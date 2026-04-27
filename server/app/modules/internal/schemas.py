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


class UserCreateSchema(BaseModel):
    tenant_id: str
    email: EmailStr
    name: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="MEMBER", pattern="^(ADMIN|MEMBER)$")
    status: str = Field(default="ACTIVE", pattern="^(INVITED|ACTIVE|DISABLED)$")


class UserUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=120)
    role: str | None = Field(default=None, pattern="^(ADMIN|MEMBER)$")
    status: str | None = Field(default=None, pattern="^(INVITED|ACTIVE|DISABLED)$")
    password: str | None = Field(default=None, min_length=8, max_length=128)
    email_verified: bool | None = None
    mfa_enabled: bool | None = None
    mfa_method: str | None = Field(default=None, pattern="^(EMAIL|TOTP)$")


class UserResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    email: EmailStr
    name: str
    role: str
    status: str
    email_verified: bool
    mfa_enabled: bool
    mfa_method: str | None = None
    created_at: datetime
    updated_at: datetime


class UserPathSchema(BaseModel):
    user_id: str


class ClientAppCreateSchema(BaseModel):
    tenant_id: str
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=300)
    redirect_uris: list[str] = Field(default_factory=list)
    allowed_scopes: list[str] = Field(default_factory=list)
    is_public: bool = False


class ClientAppUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=300)
    redirect_uris: list[str] | None = None
    allowed_scopes: list[str] | None = None
    status: str | None = Field(default=None, pattern="^(ACTIVE|DISABLED)$")


class ClientAppResponseSchema(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str | None
    client_id: str
    is_public: bool
    redirect_uris: list[str]
    allowed_scopes: list[str]
    status: str
    created_at: datetime
    updated_at: datetime


class ClientAppPathSchema(BaseModel):
    client_app_id: str


class ApiKeyCreateSchema(BaseModel):
    tenant_id: str
    client_app_id: str | None = None
    name: str = Field(min_length=2, max_length=120)
    scopes: list[str] = Field(default_factory=list)


class ApiKeyResponseSchema(BaseModel):
    id: str
    tenant_id: str
    client_app_id: str | None
    name: str
    key_prefix: str
    scopes: list[str]
    status: str
    created_at: datetime
    updated_at: datetime


class ApiKeySecretResponseSchema(ApiKeyResponseSchema):
    secret: str


class ApiKeyPathSchema(BaseModel):
    api_key_id: str


class RoleBindingCreateSchema(BaseModel):
    tenant_id: str
    user_id: str
    client_app_id: str
    roles: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    status: str = Field(default="ACTIVE", pattern="^(ACTIVE|DISABLED)$")


class RoleBindingUpdateSchema(BaseModel):
    roles: list[str] | None = None
    scopes: list[str] | None = None
    status: str | None = Field(default=None, pattern="^(ACTIVE|DISABLED)$")


class RoleBindingResponseSchema(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    client_app_id: str
    roles: list[str]
    scopes: list[str]
    status: str
    created_at: datetime
    updated_at: datetime


class RoleBindingPathSchema(BaseModel):
    role_binding_id: str


class ApiKeyListResponseSchema(BaseModel):
    id: str
    tenant_id: str
    client_app_id: str | None
    name: str
    key_prefix: str
    scopes: list[str]
    status: str
    created_at: datetime
    updated_at: datetime


class AuditLogResponseSchema(BaseModel):
    id: str
    action: str
    actor_type: str
    status: str
    details: dict
    created_at: datetime


class TenantSlugPathSchema(BaseModel):
    tenant_slug: str


class WhiteLabelResponseSchema(BaseModel):
    tenant_name: str
    tenant_slug: str
    branding: TenantBrandingPayload
    lgpd_consent_required: bool


class ConsentResponseSchema(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    client_app_id: str
    scopes: list[str]
    granted_at: datetime
    revoked_at: datetime | None


class ConsentPathSchema(BaseModel):
    consent_id: str


class TelemetrySummarySchema(BaseModel):
    tenant_id: str
    total_events: int
    login_events: int
    oauth_events: int
    failed_events: int
    top_event_types: list[dict[str, int | str]]


class MfaSetupResponseSchema(BaseModel):
    secret: str
    otpauth_uri: str
    already_enabled: bool


class MfaSetupSchema(BaseModel):
    method: str = Field(default="EMAIL", pattern="^(EMAIL|TOTP)$")


class MfaVerifySchema(BaseModel):
    code: str = Field(min_length=6, max_length=8)
