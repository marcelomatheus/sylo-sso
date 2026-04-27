from pydantic import BaseModel, EmailStr, Field


class LoginSchema(BaseModel):
    tenant_slug: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    mfa_code: str | None = Field(default=None, min_length=6, max_length=8)


class AuthorizeSchema(BaseModel):
    tenant_slug: str = Field(min_length=3, max_length=80)
    client_id: str = Field(min_length=8, max_length=120)
    redirect_uri: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    scopes: list[str] = Field(default_factory=list)
    state: str | None = None
    code_challenge: str | None = None
    code_challenge_method: str | None = Field(default=None, pattern="^(plain|S256)$")
    consent_accepted: bool = False
    mfa_code: str | None = Field(default=None, min_length=6, max_length=8)


class TokenSchema(BaseModel):
    grant_type: str = Field(pattern="^(authorization_code|refresh_token)$")
    client_id: str | None = None
    client_secret: str | None = None
    code: str | None = None
    redirect_uri: str | None = None
    code_verifier: str | None = None
    refresh_token: str | None = None


class RevokeSchema(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None


class ConsentRevokeSchema(BaseModel):
    client_id: str
    user_id: str
