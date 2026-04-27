from __future__ import annotations

from app.core.security import hash_secret
from app.models import ClientApp, EmailVerificationToken
from app.modules.external.service import PublicAuthService
from app.modules.internal.service import TenantService, UserService
from app.models import PasswordResetToken, User


def test_public_registration_creates_member_user():
    tenant = TenantService.create(
        {
            "name": "Public Corp",
            "slug": "public-corp",
            "contact_email": "owner@public.example.com",
            "plan": "starter",
        }
    )

    response = PublicAuthService.register(
        {
            "tenant_slug": tenant["slug"],
            "email": "member@public.example.com",
            "name": "Public Member",
            "password": "Sup3rSecret!",
        },
        "http://localhost:3000",
    )

    assert response["status"] == "created"
    created_user = User.objects(email="member@public.example.com").first()
    assert created_user is not None
    assert created_user.role == "MEMBER"


def test_forgot_password_creates_reset_token():
    tenant = TenantService.create(
        {
            "name": "Reset Corp",
            "slug": "reset-corp",
            "contact_email": "owner@reset.example.com",
            "plan": "starter",
        }
    )
    user = UserService.create(
        {
            "tenant_id": tenant["id"],
            "email": "member@reset.example.com",
            "name": "Reset Member",
            "password": "Sup3rSecret!",
            "role": "MEMBER",
            "status": "ACTIVE",
        }
    )

    response = PublicAuthService.forgot_password(
        {
            "tenant_slug": tenant["slug"],
            "email": user["email"],
        },
        "http://localhost:3000",
    )

    assert response["status"] == "accepted"
    assert PasswordResetToken.objects.count() == 1


def test_reset_password_updates_password_and_consumes_token():
    tenant = TenantService.create(
        {
            "name": "Restore Corp",
            "slug": "restore-corp",
            "contact_email": "owner@restore.example.com",
            "plan": "starter",
        }
    )
    user = UserService.create(
        {
            "tenant_id": tenant["id"],
            "email": "member@restore.example.com",
            "name": "Restore Member",
            "password": "Sup3rSecret!",
            "role": "MEMBER",
            "status": "ACTIVE",
        }
    )

    PublicAuthService.forgot_password(
        {
            "tenant_slug": tenant["slug"],
            "email": user["email"],
        },
        "http://localhost:3000",
    )
    token_record = PasswordResetToken.objects.first()
    assert token_record is not None

    # Generate a known token through the public service path.
    PublicAuthService.forgot_password(
        {
            "tenant_slug": tenant["slug"],
            "email": user["email"],
        },
        "http://localhost:3000",
    )

    # The service stores only hashes, so create a fresh token by calling forgot_password
    # and deriving it from the email task path is out of scope for this unit test.
    # Reuse the direct model save with a known token to validate reset behavior.
    from datetime import UTC, datetime, timedelta

    from app.core.security import hash_secret

    known_token = "pr_known_reset_token_123456789"
    PasswordResetToken.objects.delete()
    token_record = PasswordResetToken(
        tenant=User.objects(id=user["id"]).first().tenant,
        user=User.objects(id=user["id"]).first(),
        token_hash=hash_secret(known_token),
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1),
    ).save()

    response = PublicAuthService.reset_password(
        {
            "tenant_slug": tenant["slug"],
            "token": known_token,
            "new_password": "N3wSecret123!",
        }
    )

    assert response["status"] == "password_updated"
    token_record.reload()
    assert token_record.consumed_at is not None


def test_public_registration_accepts_client_redirect_context():
    from app.modules.internal.service import ClientAppService

    tenant = TenantService.create(
        {
            "name": "Satellite Corp",
            "slug": "satellite-corp",
            "contact_email": "owner@satellite.example.com",
            "plan": "starter",
        }
    )
    client_app = ClientAppService.create(
        {
            "tenant_id": tenant["id"],
            "name": "Satellite App",
            "description": "App",
            "redirect_uris": ["https://satellite.example.com/callback"],
            "allowed_scopes": ["openid", "profile"],
            "is_public": True,
        }
    )

    response = PublicAuthService.register(
        {
            "tenant_slug": tenant["slug"],
            "email": "new@satellite.example.com",
            "name": "Satellite User",
            "password": "Sup3rSecret!",
            "client_id": client_app["client_id"],
            "redirect_uri": "https://satellite.example.com/callback",
            "state": "abc123",
            "scopes": ["openid"],
            "consent_accepted": True,
        },
        "http://localhost:3000",
    )
    verification = EmailVerificationToken.objects.first()

    assert response["next_step"]["type"] == "verify_email"
    assert verification is not None
    assert verification.redirect_uri == "https://satellite.example.com/callback"
    assert verification.state == "abc123"


def test_verify_email_can_return_redirect_to_client():
    from datetime import UTC, datetime, timedelta

    tenant = TenantService.create(
        {
            "name": "Verify Redirect Corp",
            "slug": "verify-redirect",
            "contact_email": "owner@verify-redirect.example.com",
            "plan": "starter",
        }
    )
    user = UserService.create(
        {
            "tenant_id": tenant["id"],
            "email": "member@verify-redirect.example.com",
            "name": "Verify User",
            "password": "Sup3rSecret!",
            "role": "MEMBER",
            "status": "ACTIVE",
        }
    )
    db_user = User.objects(id=user["id"]).first()
    client_app = ClientApp(
        tenant=db_user.tenant,
        name="Verify App",
        client_id="client_verify_app_123",
        is_public=True,
        redirect_uris=["https://verify.example.com/callback"],
        allowed_scopes=["openid"],
    ).save()
    known_token = "ev_known_redirect_token_123456789"
    EmailVerificationToken(
        tenant=db_user.tenant,
        user=db_user,
        client_app=client_app,
        token_hash=hash_secret(known_token),
        redirect_uri="https://verify.example.com/callback",
        state="state-123",
        scopes=["openid"],
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1),
    ).save()

    response = PublicAuthService.verify_email({"tenant_slug": tenant["slug"], "token": known_token})

    assert response["status"] == "verified"
    assert response["redirect_to"].startswith("https://verify.example.com/callback?code=ac_")
    assert "state=state-123" in response["redirect_to"]
