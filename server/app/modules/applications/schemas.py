from datetime import datetime

from pydantic import BaseModel, Field


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
