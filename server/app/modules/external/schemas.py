from pydantic import BaseModel, EmailStr, Field


class PublicRegistrationSchema(BaseModel):
    tenant_slug: str = Field(min_length=3, max_length=80)
    email: EmailStr
    name: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    client_id: str | None = Field(default=None, min_length=8, max_length=120)
    redirect_uri: str | None = None
    state: str | None = None
    scopes: list[str] = Field(default_factory=list)
    consent_accepted: bool = False


class ForgotPasswordSchema(BaseModel):
    tenant_slug: str = Field(min_length=3, max_length=80)
    email: EmailStr


class ResetPasswordSchema(BaseModel):
    tenant_slug: str = Field(min_length=3, max_length=80)
    token: str = Field(min_length=16, max_length=160)
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailSchema(BaseModel):
    tenant_slug: str = Field(min_length=3, max_length=80)
    token: str = Field(min_length=16, max_length=160)


class ResendVerificationSchema(BaseModel):
    tenant_slug: str = Field(min_length=3, max_length=80)
    email: EmailStr
