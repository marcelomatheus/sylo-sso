from __future__ import annotations

import pytest

from app.core.errors import ConflictError
from app.models import MfaChallenge
from app.modules.internal.service import ApiKeyService, MfaService, RoleBindingService, TenantService, UserService


def test_bootstrap_creates_first_tenant_admin_and_session():
    payload = {
        "tenant": {
            "name": "Acme Corp",
            "slug": "acme",
            "contact_email": "admin@acme.example.com",
            "plan": "starter",
        },
        "admin_name": "Alice Admin",
        "admin_email": "alice@acme.example.com",
        "admin_password": "Sup3rSecret!",
    }

    response = TenantService.bootstrap(payload)

    assert response["tenant"]["slug"] == "acme"
    assert response["admin_user"]["role"] == "ADMIN"
    assert response["session"]["token_type"] == "Bearer"
    assert response["session"]["refresh_token"].startswith("rt_")


def test_create_user_rejects_duplicate_email_in_same_tenant():
    tenant = TenantService.create(
        {
                "name": "Beta Corp",
                "slug": "beta",
                "contact_email": "owner@beta.example.com",
                "plan": "starter",
            }
        )
    payload = {
        "tenant_id": tenant["id"],
        "email": "member@beta.example.com",
        "name": "Member One",
        "password": "Sup3rSecret!",
        "role": "MEMBER",
        "status": "ACTIVE",
    }

    UserService.create(payload)

    with pytest.raises(ConflictError):
        UserService.create(payload)


def test_same_email_can_exist_in_different_tenants():
    tenant_a = TenantService.create(
        {
                "name": "Gamma Corp",
                "slug": "gamma",
                "contact_email": "owner@gamma.example.com",
                "plan": "starter",
            }
        )
    tenant_b = TenantService.create(
        {
                "name": "Delta Corp",
                "slug": "delta",
                "contact_email": "owner@delta.example.com",
                "plan": "starter",
            }
        )
    email = "shared@tenant.example.com"

    user_a = UserService.create(
        {
            "tenant_id": tenant_a["id"],
            "email": email,
            "name": "User A",
            "password": "Sup3rSecret!",
            "role": "MEMBER",
            "status": "ACTIVE",
        }
    )
    user_b = UserService.create(
        {
            "tenant_id": tenant_b["id"],
            "email": email,
            "name": "User B",
            "password": "Sup3rSecret!",
            "role": "MEMBER",
            "status": "ACTIVE",
        }
    )

    assert user_a["tenant_id"] != user_b["tenant_id"]
    assert user_a["email"] == user_b["email"] == email


def test_role_binding_can_be_created_and_updated():
    from app.modules.internal.service import ClientAppService

    tenant = TenantService.create(
        {
            "name": "Bindings Corp",
            "slug": "bindings",
            "contact_email": "owner@bindings.example.com",
            "plan": "starter",
        }
    )
    user = UserService.create(
        {
            "tenant_id": tenant["id"],
            "email": "member@bindings.example.com",
            "name": "Member Binding",
            "password": "Sup3rSecret!",
            "role": "MEMBER",
            "status": "ACTIVE",
        }
    )
    client_app = ClientAppService.create(
        {
            "tenant_id": tenant["id"],
            "name": "Binding Portal",
            "description": "Portal",
            "redirect_uris": ["https://binding.example.com/callback"],
            "allowed_scopes": ["openid", "profile"],
            "is_public": True,
        }
    )

    binding = RoleBindingService.create(
        {
            "tenant_id": tenant["id"],
            "user_id": user["id"],
            "client_app_id": client_app["id"],
            "roles": ["member"],
            "scopes": ["openid"],
            "status": "ACTIVE",
        }
    )
    updated = RoleBindingService.update(binding["id"], {"status": "DISABLED", "scopes": ["openid", "profile"]})

    assert binding["status"] == "ACTIVE"
    assert updated["status"] == "DISABLED"
    assert updated["scopes"] == ["openid", "profile"]


def test_api_key_can_rotate_secret():
    from app.modules.internal.service import ClientAppService

    tenant = TenantService.create(
        {
            "name": "Rotate Corp",
            "slug": "rotate-corp",
            "contact_email": "owner@rotate.example.com",
            "plan": "starter",
        }
    )
    client_app = ClientAppService.create(
        {
            "tenant_id": tenant["id"],
            "name": "Rotate Portal",
            "description": "Portal",
            "redirect_uris": ["https://rotate.example.com/callback"],
            "allowed_scopes": ["tokens:introspect"],
            "is_public": False,
        }
    )
    api_key = ApiKeyService.create(
        {
            "tenant_id": tenant["id"],
            "client_app_id": client_app["id"],
            "name": "Rotate key",
            "scopes": ["tokens:introspect"],
        }
    )

    rotated = ApiKeyService.rotate(api_key["id"])

    assert rotated["id"] == api_key["id"]
    assert rotated["secret"] != api_key["secret"]


def test_mfa_service_enables_and_disables_user_mfa():
    tenant = TenantService.create(
        {
            "name": "MFA Corp",
            "slug": "mfa-corp",
            "contact_email": "owner@mfa.example.com",
            "plan": "starter",
        }
    )
    user = UserService.create(
        {
            "tenant_id": tenant["id"],
            "email": "admin@mfa.example.com",
            "name": "MFA Admin",
            "password": "Sup3rSecret!",
            "role": "ADMIN",
            "status": "ACTIVE",
        }
    )
    from app.models import User
    from app.core.security import verify_totp_code

    db_user = User.objects(id=user["id"]).first()
    setup = MfaService.setup(db_user, {"method": "TOTP"})

    assert setup["secret"]
    assert verify_totp_code(setup["secret"], setup["otpauth_uri"].split("secret=")[1].split("&")[0]) is False

    from app.core.security import _totp_code  # type: ignore[attr-defined]
    from datetime import UTC, datetime

    code = _totp_code(setup["secret"], int(datetime.now(UTC).timestamp()))
    response = MfaService.verify(db_user, {"code": code})
    disabled = MfaService.disable(db_user)

    assert response["status"] == "enabled"
    assert disabled["status"] == "disabled"


def test_email_mfa_setup_and_verify(monkeypatch: pytest.MonkeyPatch):
    tenant = TenantService.create(
        {
            "name": "Email MFA Corp",
            "slug": "email-mfa-corp",
            "contact_email": "owner@emailmfa.example.com",
            "plan": "starter",
        }
    )
    user = UserService.create(
        {
            "tenant_id": tenant["id"],
            "email": "admin@emailmfa.example.com",
            "name": "Email MFA Admin",
            "password": "Sup3rSecret!",
            "role": "ADMIN",
            "status": "ACTIVE",
        }
    )
    from app.models import User

    monkeypatch.setattr("app.modules.internal.service.generate_one_time_code", lambda length=6: "654321")
    db_user = User.objects(id=user["id"]).first()
    setup = MfaService.setup(db_user, {"method": "EMAIL"})

    assert setup["method"] == "EMAIL"
    assert MfaChallenge.objects(user=db_user, method="EMAIL", consumed_at=None).count() == 1

    response = MfaService.verify(db_user, {"code": "654321"})
    disabled = MfaService.disable(db_user)

    assert response["status"] == "enabled"
    assert response["method"] == "EMAIL"
    assert disabled["status"] == "disabled"
