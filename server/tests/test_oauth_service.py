from __future__ import annotations

import base64
import hashlib
from datetime import UTC, datetime

from app.core.security import _totp_code  # type: ignore[attr-defined]
import pytest

from app.models import MfaChallenge
from app.modules.internal.service import ClientAppService, MfaService, RoleBindingService, TenantService, UserService
from app.modules.oauth.service import OAuthService


def test_authorization_code_pkce_exchange_flow():
    tenant = TenantService.create(
        {
            "name": "Omega Corp",
            "slug": "omega",
            "contact_email": "owner@omega.example.com",
            "plan": "starter",
        }
    )
    user = UserService.create(
        {
            "tenant_id": tenant["id"],
            "email": "admin@omega.example.com",
            "name": "Omega Admin",
            "password": "Sup3rSecret!",
            "role": "ADMIN",
            "status": "ACTIVE",
        }
    )
    client_app = ClientAppService.create(
        {
            "tenant_id": tenant["id"],
            "name": "Portal",
            "description": "Admin portal",
            "redirect_uris": ["https://portal.omega.test/callback"],
            "allowed_scopes": ["openid", "profile"],
            "is_public": True,
        }
    )
    verifier = "pkce-verifier-12345"
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("utf-8")).digest()).decode("utf-8").rstrip("=")

    authorization = OAuthService.authorize(
        {
            "tenant_slug": tenant["slug"],
            "client_id": client_app["client_id"],
            "redirect_uri": "https://portal.omega.test/callback",
            "email": user["email"],
            "password": "Sup3rSecret!",
            "scopes": ["openid", "profile"],
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "consent_accepted": True,
        }
    )

    token_response = OAuthService.exchange_token(
        {
            "grant_type": "authorization_code",
            "client_id": client_app["client_id"],
            "code": authorization["code"],
            "redirect_uri": "https://portal.omega.test/callback",
            "code_verifier": verifier,
        }
    )

    assert token_response["token_type"] == "Bearer"
    assert token_response["refresh_token"].startswith("rt_")
    assert token_response["scope"] == "openid profile"


def test_login_requires_mfa_when_enabled():
    tenant = TenantService.create(
        {
            "name": "Secure Corp",
            "slug": "secure",
            "contact_email": "owner@secure.example.com",
            "plan": "starter",
        }
    )
    user = UserService.create(
        {
            "tenant_id": tenant["id"],
            "email": "admin@secure.example.com",
            "name": "Secure Admin",
            "password": "Sup3rSecret!",
            "role": "ADMIN",
            "status": "ACTIVE",
        }
    )
    from app.models import User

    db_user = User.objects(id=user["id"]).first()
    setup = MfaService.setup(db_user, {"method": "TOTP"})
    MfaService.verify(db_user, {"code": _totp_code(setup["secret"], int(datetime.now(UTC).timestamp()))})

    try:
        OAuthService.login({"tenant_slug": tenant["slug"], "email": user["email"], "password": "Sup3rSecret!"})
        assert False, "expected MFA to be required"
    except Exception as exc:
        assert getattr(exc, "details", {}).get("mfa_required") is True

    response = OAuthService.login(
        {
            "tenant_slug": tenant["slug"],
            "email": user["email"],
            "password": "Sup3rSecret!",
            "mfa_code": _totp_code(setup["secret"], int(datetime.now(UTC).timestamp())),
        }
    )
    assert response["token_type"] == "Bearer"


def test_member_authorization_requires_active_role_binding():
    tenant = TenantService.create(
        {
            "name": "Access Corp",
            "slug": "access",
            "contact_email": "owner@access.example.com",
            "plan": "starter",
        }
    )
    user = UserService.create(
        {
            "tenant_id": tenant["id"],
            "email": "member@access.example.com",
            "name": "Access Member",
            "password": "Sup3rSecret!",
            "role": "MEMBER",
            "status": "ACTIVE",
        }
    )
    from app.models import User

    db_user = User.objects(id=user["id"]).first()
    db_user.email_verified = True
    db_user.save()
    client_app = ClientAppService.create(
        {
            "tenant_id": tenant["id"],
            "name": "Access Portal",
            "description": "Portal",
            "redirect_uris": ["https://access.example.com/callback"],
            "allowed_scopes": ["openid", "profile"],
            "is_public": True,
        }
    )
    RoleBindingService.create(
        {
            "tenant_id": tenant["id"],
            "user_id": user["id"],
            "client_app_id": client_app["id"],
            "roles": ["member"],
            "scopes": ["openid"],
            "status": "ACTIVE",
        }
    )

    authorization = OAuthService.authorize(
        {
            "tenant_slug": tenant["slug"],
            "client_id": client_app["client_id"],
            "redirect_uri": "https://access.example.com/callback",
            "email": user["email"],
            "password": "Sup3rSecret!",
            "scopes": ["openid"],
            "consent_accepted": True,
        }
    )

    assert authorization["code"].startswith("ac_")


def test_login_requires_email_mfa_and_accepts_code(monkeypatch: pytest.MonkeyPatch):
    tenant = TenantService.create(
        {
            "name": "Email Secure Corp",
            "slug": "email-secure",
            "contact_email": "owner@email-secure.example.com",
            "plan": "starter",
        }
    )
    user = UserService.create(
        {
            "tenant_id": tenant["id"],
            "email": "admin@email-secure.example.com",
            "name": "Email Secure Admin",
            "password": "Sup3rSecret!",
            "role": "ADMIN",
            "status": "ACTIVE",
        }
    )
    from app.models import User

    db_user = User.objects(id=user["id"]).first()
    monkeypatch.setattr("app.modules.internal.service.generate_one_time_code", lambda length=6: "111222")
    MfaService.setup(db_user, {"method": "EMAIL"})
    MfaService.verify(db_user, {"code": "111222"})

    monkeypatch.setattr("app.modules.oauth.service.generate_one_time_code", lambda length=6: "333444")
    try:
        OAuthService.login({"tenant_slug": tenant["slug"], "email": user["email"], "password": "Sup3rSecret!"})
        assert False, "expected email MFA to be required"
    except Exception as exc:
        assert getattr(exc, "details", {}).get("mfa_required") is True
        assert getattr(exc, "details", {}).get("mfa_method") == "EMAIL"

    assert MfaChallenge.objects(user=db_user, method="EMAIL", consumed_at=None).count() == 1
    response = OAuthService.login(
        {
            "tenant_slug": tenant["slug"],
            "email": user["email"],
            "password": "Sup3rSecret!",
            "mfa_code": "333444",
        }
    )
    assert response["token_type"] == "Bearer"
