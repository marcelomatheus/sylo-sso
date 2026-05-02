from __future__ import annotations

from app import create_app
from app.modules.applications.service import ClientAppService
from app.modules.auth.service import OAuthService
from app.modules.tenants.service import TenantService
from app.modules.users.service import UserService


def test_authorize_requires_consent_when_tenant_demands_it():
    tenant = TenantService.create(
        {
            "name": "Consent Corp",
            "slug": "consent-corp",
            "contact_email": "owner@consent.example.com",
            "plan": "starter",
            "lgpd_consent_required": True,
        }
    )
    user = UserService.create(
        {
            "tenant_id": tenant["id"],
            "email": "admin@consent.example.com",
            "name": "Consent Admin",
            "password": "Sup3rSecret!",
            "role": "ADMIN",
            "status": "ACTIVE",
        }
    )
    client_app = ClientAppService.create(
        {
            "tenant_id": tenant["id"],
            "name": "Consent Portal",
            "redirect_uris": ["https://consent.example.com/callback"],
            "allowed_scopes": ["openid", "profile"],
            "is_public": True,
        }
    )

    try:
        OAuthService.authorize(
            {
                "tenant_slug": tenant["slug"],
                "client_id": client_app["client_id"],
                "redirect_uri": "https://consent.example.com/callback",
                "email": user["email"],
                "password": "Sup3rSecret!",
                "scopes": ["openid"],
                "consent_accepted": False,
            }
        )
    except Exception as exc:
        assert "Consentimento LGPD obrigatorio" in str(exc)
    else:
        raise AssertionError("Consent should have been required.")


def test_public_branding_endpoint_returns_tenant_branding():
    TenantService.create(
        {
            "name": "Brand Corp",
            "slug": "brand-corp",
            "contact_email": "owner@brand.example.com",
            "plan": "starter",
            "branding": {
                "primary_color": "#123456",
                "secondary_color": "#654321",
                "font_family": "Sora",
                "login_title": "Entre no ecossistema",
                "login_subtitle": "SSO white-label para clientes B2B.",
            },
        }
    )

    app = create_app()
    client = app.test_client()
    response = client.get("/api/v1/tenants/external/branding/brand-corp")

    assert response.status_code == 200
    body = response.get_json()
    assert body["tenant_slug"] == "brand-corp"
    assert body["branding"]["primary_color"] == "#123456"
