from flask import request
from flask_openapi3 import APIBlueprint, Tag

from app.core.guards import api_key_auth
from app.core.rate_limit import enforce_rate_limit
from app.modules.external.service import PublicAuthService, PublicTenantService, TokenIntrospectionService
from app.modules.internal.schemas import TenantSlugPathSchema


external_tag = Tag(name="External")
external_api = APIBlueprint("external_api", __name__, abp_tags=[external_tag])


@external_api.post("/tokens/introspect", summary="Introspect access token")
@api_key_auth(required_scopes=["tokens:introspect"])
def introspect_token():
    body = request.get_json(silent=True) or {}
    enforce_rate_limit(request, "introspect")
    return TokenIntrospectionService.introspect(body.get("token", "")), 200


@external_api.get("/tenants/<tenant_slug>/branding", summary="Get public tenant branding")
def get_public_branding(path: TenantSlugPathSchema):
    return PublicTenantService.branding(path.tenant_slug), 200


@external_api.post("/register", summary="Register user in tenant")
def register_user():
    body = request.get_json(silent=True) or {}
    enforce_rate_limit(request, "public-register", tenant_id=body.get("tenant_slug"))
    origin = request.headers.get("Origin") or request.headers.get("Referer") or "http://localhost:3000"
    return PublicAuthService.register(body, origin), 201


@external_api.post("/password/forgot", summary="Request password reset")
def forgot_password():
    body = request.get_json(silent=True) or {}
    enforce_rate_limit(request, "password-forgot", tenant_id=body.get("tenant_slug"))
    origin = request.headers.get("Origin") or request.headers.get("Referer") or "http://localhost:3000"
    return PublicAuthService.forgot_password(body, origin), 202


@external_api.post("/password/reset", summary="Reset password with token")
def reset_password():
    body = request.get_json(silent=True) or {}
    enforce_rate_limit(request, "password-reset", tenant_id=body.get("tenant_slug"))
    return PublicAuthService.reset_password(body), 200


@external_api.post("/email/verify", summary="Verify email with token")
def verify_email():
    body = request.get_json(silent=True) or {}
    enforce_rate_limit(request, "email-verify", tenant_id=body.get("tenant_slug"))
    return PublicAuthService.verify_email(body), 200


@external_api.post("/email/resend", summary="Resend verification email")
def resend_verification_email():
    body = request.get_json(silent=True) or {}
    enforce_rate_limit(request, "email-resend", tenant_id=body.get("tenant_slug"))
    origin = request.headers.get("Origin") or request.headers.get("Referer") or "http://localhost:3000"
    return PublicAuthService.resend_verification(body, origin), 202
