from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


class MfaSetupResponseSchema(BaseModel):
    secret: str
    otpauth_uri: str
    already_enabled: bool


class MfaSetupSchema(BaseModel):
    method: str = Field(default="EMAIL", pattern="^(EMAIL|TOTP)$")


class MfaVerifySchema(BaseModel):
    code: str = Field(min_length=6, max_length=8)
