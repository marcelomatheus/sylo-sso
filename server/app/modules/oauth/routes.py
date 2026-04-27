from flask import request
from flask_openapi3 import APIBlueprint, Tag

from app.core.guards import bearer_auth
from app.core.rate_limit import enforce_rate_limit
from app.modules.oauth.service import OAuthService


oauth_tag = Tag(name="OAuth")
oauth_api = APIBlueprint("oauth_api", __name__, abp_tags=[oauth_tag])


@oauth_api.post("/login", summary="Administrator login")
def login():
    enforce_rate_limit(request, "login", tenant_id=(request.get_json(silent=True) or {}).get("tenant_slug"))
    return OAuthService.login(request.get_json(silent=True) or {}), 200


@oauth_api.post("/authorize", summary="Authorize client app")
def authorize():
    body = request.get_json(silent=True) or {}
    enforce_rate_limit(request, "authorize", tenant_id=body.get("tenant_slug"), client_id=body.get("client_id"))
    return OAuthService.authorize(body), 200


@oauth_api.post("/token", summary="Exchange authorization code or refresh token")
def token():
    body = request.get_json(silent=True) or {}
    enforce_rate_limit(request, "token", client_id=body.get("client_id"))
    return OAuthService.exchange_token(body), 200


@oauth_api.post("/revoke", summary="Revoke access or refresh token")
@bearer_auth()
def revoke():
    return OAuthService.revoke(request.get_json(silent=True) or {}), 200
