from flask import request
from flask_openapi3 import APIBlueprint, Tag

from app.core.guards import api_key_auth, bearer_auth
from app.core.rate_limit import enforce_rate_limit
from app.modules.auth.service import OAuthService, PublicAuthService, TokenIntrospectionService


external_tag = Tag(name="Auth External")
auth_external_api = APIBlueprint("auth_external_api", __name__, abp_tags=[external_tag])


@auth_external_api.post("/login", summary="Administrator login")
def login():
    enforce_rate_limit(request, "login", tenant_id=(request.get_json(silent=True) or {}).get("tenant_slug"))
    return OAuthService.login(request.get_json(silent=True) or {}), 200


@auth_external_api.post("/authorize", summary="Authorize client app")
def authorize():
    body = request.get_json(silent=True) or {}
    enforce_rate_limit(request, "authorize", tenant_id=body.get("tenant_slug"), client_id=body.get("client_id"))
    return OAuthService.authorize(body), 200


@auth_external_api.post("/token", summary="Exchange authorization code or refresh token")
def token():
    body = request.get_json(silent=True) or {}
    enforce_rate_limit(request, "token", client_id=body.get("client_id"))
    return OAuthService.exchange_token(body), 200


@auth_external_api.post("/revoke", summary="Revoke access or refresh token")
@bearer_auth()
def revoke():
    return OAuthService.revoke(request.get_json(silent=True) or {}), 200


@auth_external_api.post("/register", summary="Register user in tenant")
def register_user():
    body = request.get_json(silent=True) or {}
    enforce_rate_limit(request, "public-register", tenant_id=body.get("tenant_slug"))
    origin = request.headers.get("Origin") or request.headers.get("Referer") or "http://localhost:3000"
    return PublicAuthService.register(body, origin), 201


@auth_external_api.post("/password/forgot", summary="Request password reset")
def forgot_password():
    body = request.get_json(silent=True) or {}
    enforce_rate_limit(request, "password-forgot", tenant_id=body.get("tenant_slug"))
    origin = request.headers.get("Origin") or request.headers.get("Referer") or "http://localhost:3000"
    return PublicAuthService.forgot_password(body, origin), 202


@auth_external_api.post("/password/reset", summary="Reset password with token")
def reset_password():
    body = request.get_json(silent=True) or {}
    enforce_rate_limit(request, "password-reset", tenant_id=body.get("tenant_slug"))
    return PublicAuthService.reset_password(body), 200


@auth_external_api.post("/email/verify", summary="Verify email with token")
def verify_email():
    body = request.get_json(silent=True) or {}
    enforce_rate_limit(request, "email-verify", tenant_id=body.get("tenant_slug"))
    return PublicAuthService.verify_email(body), 200


@auth_external_api.post("/email/resend", summary="Resend verification email")
def resend_verification_email():
    body = request.get_json(silent=True) or {}
    enforce_rate_limit(request, "email-resend", tenant_id=body.get("tenant_slug"))
    origin = request.headers.get("Origin") or request.headers.get("Referer") or "http://localhost:3000"
    return PublicAuthService.resend_verification(body, origin), 202


@auth_external_api.post("/tokens/introspect", summary="Introspect access token")
@api_key_auth(required_scopes=["tokens:introspect"])
def introspect_token():
    body = request.get_json(silent=True) or {}
    enforce_rate_limit(request, "introspect")
    return TokenIntrospectionService.introspect(body.get("token", "")), 200
