from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.security import hash_secret
from app.models import ClientApp, Consent, EmailVerificationToken, Tenant, User
from app.modules.external.service import PublicAuthService
from app.modules.internal.service import ClientAppService, ConsentService, TenantService, UserService
from app.modules.oauth.service import OAuthService


def test_verify_email_marks_user_as_verified():
    tenant = TenantService.create(
        {
          "name": "Verify Corp",
          "slug": "verify-corp",
          "contact_email": "owner@verify.example.com",
          "plan": "starter",
        }
    )

    registration = PublicAuthService.register(
        {
            "tenant_slug": tenant["slug"],
            "email": "member@verify.example.com",
            "name": "Verify Member",
            "password": "Sup3rSecret!",
        },
        "http://localhost:3000",
    )

    user = User.objects(id=registration["user"]["id"]).first()
    assert user is not None
    assert user.email_verified is False

    EmailVerificationToken.objects.delete()
    known_token = "ev_known_verification_token_123456789"
    EmailVerificationToken(
        tenant=user.tenant,
        user=user,
        token_hash=hash_secret(known_token),
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1),
    ).save()

    response = PublicAuthService.verify_email(
        {
            "tenant_slug": tenant["slug"],
            "token": known_token,
        }
    )

    user.reload()
    assert response["status"] == "verified"
    assert user.email_verified is True


def test_member_login_requires_verified_email():
    tenant = TenantService.create(
        {
            "name": "Gate Corp",
            "slug": "gate-corp",
            "contact_email": "owner@gate.example.com",
            "plan": "starter",
        }
    )
    PublicAuthService.register(
        {
            "tenant_slug": tenant["slug"],
            "email": "member@gate.example.com",
            "name": "Gate Member",
            "password": "Sup3rSecret!",
        },
        "http://localhost:3000",
    )

    try:
        OAuthService.login(
            {
                "tenant_slug": tenant["slug"],
                "email": "member@gate.example.com",
                "password": "Sup3rSecret!",
            }
        )
    except Exception as exc:
        assert "Confirme seu e-mail" in str(exc)
    else:
        raise AssertionError("Member login should require a verified email.")


def test_revoke_consent_marks_record_as_revoked():
    tenant = TenantService.create(
        {
            "name": "Consent Revoke Corp",
            "slug": "consent-revoke-corp",
            "contact_email": "owner@consentrevoke.example.com",
            "plan": "starter",
        }
    )
    user = UserService.create(
        {
            "tenant_id": tenant["id"],
            "email": "member@consentrevoke.example.com",
            "name": "Consent Member",
            "password": "Sup3rSecret!",
            "role": "MEMBER",
            "status": "ACTIVE",
        }
    )
    user_document = User.objects(id=user["id"]).first()
    user_document.email_verified = True
    user_document.save()
    client_app = ClientAppService.create(
        {
            "tenant_id": tenant["id"],
            "name": "Consent Portal",
            "redirect_uris": ["https://consent.revoke/callback"],
            "allowed_scopes": ["openid"],
            "is_public": True,
        }
    )
    tenant_document = Tenant.objects(id=tenant["id"]).first()
    client_app_document = ClientApp.objects(id=client_app["id"]).first()
    consent = Consent(
        tenant=tenant_document,
        user=user_document,
        client_app=client_app_document,
        scopes=["openid"],
        granted_at=datetime.now(UTC).replace(tzinfo=None),
    ).save()

    response = ConsentService.revoke(str(consent.id))

    consent.reload()
    assert response["revoked_at"] is not None
    assert consent.revoked_at is not None
