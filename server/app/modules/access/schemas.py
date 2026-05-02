from datetime import datetime

from pydantic import BaseModel, Field


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
