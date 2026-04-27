from flask import g, request
from flask_openapi3 import APIBlueprint, Tag

from app.core.guards import bearer_auth
from app.modules.internal.schemas import ApiKeyPathSchema, ClientAppPathSchema, ConsentPathSchema, RoleBindingPathSchema, TenantPathSchema, TenantSlugPathSchema, UserPathSchema
from app.modules.internal.service import ApiKeyService, AuditLogService, ClientAppService, ConsentService, MfaService, RoleBindingService, TelemetryService, TenantService, UserService, WhiteLabelService


internal_tag = Tag(name="Internal")
internal_api = APIBlueprint("internal_api", __name__, abp_tags=[internal_tag])


@internal_api.post("/bootstrap", summary="Bootstrap first tenant and admin")
def bootstrap():
    return TenantService.bootstrap(request.get_json(silent=True) or {}), 201


@internal_api.post("/tenants", summary="Create tenant")
@bearer_auth(admin_only=True)
def create_tenant():
    return TenantService.create(request.get_json(silent=True) or {}), 201


@internal_api.get("/tenants", summary="List tenants")
@bearer_auth(admin_only=True)
def list_tenants():
    return {"items": TenantService.list()}, 200


@internal_api.get("/tenants/<tenant_id>", summary="Get tenant")
@bearer_auth(admin_only=True)
def get_tenant(path: TenantPathSchema):
    return TenantService.get(path.tenant_id), 200


@internal_api.patch("/tenants/<tenant_id>", summary="Update tenant")
@bearer_auth(admin_only=True)
def update_tenant(path: TenantPathSchema):
    return TenantService.update(path.tenant_id, request.get_json(silent=True) or {}), 200


@internal_api.post("/users", summary="Create user")
@bearer_auth(admin_only=True)
def create_user():
    return UserService.create(request.get_json(silent=True) or {}), 201


@internal_api.get("/users", summary="List users")
@bearer_auth(admin_only=True)
def list_users():
    return {"items": UserService.list(request.args.get("tenant_id"))}, 200


@internal_api.patch("/users/<user_id>", summary="Update user")
@bearer_auth(admin_only=True)
def update_user(path: UserPathSchema):
    return UserService.update(path.user_id, request.get_json(silent=True) or {}), 200


@internal_api.post("/client-apps", summary="Create client app")
@bearer_auth(admin_only=True)
def create_client_app():
    return ClientAppService.create(request.get_json(silent=True) or {}), 201


@internal_api.get("/client-apps", summary="List client apps")
@bearer_auth(admin_only=True)
def list_client_apps():
    return {"items": ClientAppService.list(request.args.get("tenant_id"))}, 200


@internal_api.patch("/client-apps/<client_app_id>", summary="Update client app")
@bearer_auth(admin_only=True)
def update_client_app(path: ClientAppPathSchema):
    return ClientAppService.update(path.client_app_id, request.get_json(silent=True) or {}), 200


@internal_api.post("/api-keys", summary="Create API key")
@bearer_auth(admin_only=True)
def create_api_key():
    return ApiKeyService.create(request.get_json(silent=True) or {}), 201


@internal_api.get("/api-keys", summary="List API keys")
@bearer_auth(admin_only=True)
def list_api_keys():
    return {"items": ApiKeyService.list(request.args.get("tenant_id"))}, 200


@internal_api.post("/api-keys/<api_key_id>/revoke", summary="Revoke API key")
@bearer_auth(admin_only=True)
def revoke_api_key(path: ApiKeyPathSchema):
    return ApiKeyService.revoke(path.api_key_id), 200


@internal_api.post("/api-keys/<api_key_id>/rotate", summary="Rotate API key")
@bearer_auth(admin_only=True)
def rotate_api_key(path: ApiKeyPathSchema):
    return ApiKeyService.rotate(path.api_key_id), 200


@internal_api.get("/audit-logs", summary="List audit logs")
@bearer_auth(admin_only=True)
def list_audit_logs():
    return {"items": AuditLogService.list(request.args.get("tenant_id"))}, 200


@internal_api.get("/consents", summary="List consents")
@bearer_auth(admin_only=True)
def list_consents():
    return {"items": ConsentService.list(request.args.get("tenant_id"), request.args.get("user_id"))}, 200


@internal_api.post("/consents/<consent_id>/revoke", summary="Revoke consent")
@bearer_auth(admin_only=True)
def revoke_consent(path: ConsentPathSchema):
    return ConsentService.revoke(path.consent_id), 200


@internal_api.post("/role-bindings", summary="Create role binding")
@bearer_auth(admin_only=True)
def create_role_binding():
    return RoleBindingService.create(request.get_json(silent=True) or {}), 201


@internal_api.get("/role-bindings", summary="List role bindings")
@bearer_auth(admin_only=True)
def list_role_bindings():
    return {
        "items": RoleBindingService.list(
            request.args.get("tenant_id"),
            request.args.get("user_id"),
            request.args.get("client_app_id"),
        )
    }, 200


@internal_api.patch("/role-bindings/<role_binding_id>", summary="Update role binding")
@bearer_auth(admin_only=True)
def update_role_binding(path: RoleBindingPathSchema):
    return RoleBindingService.update(path.role_binding_id, request.get_json(silent=True) or {}), 200


@internal_api.get("/tenants/<tenant_slug>/branding", summary="Get tenant branding")
@bearer_auth(admin_only=True)
def get_tenant_branding(path: TenantSlugPathSchema):
    return WhiteLabelService.get_by_slug(path.tenant_slug), 200


@internal_api.get("/telemetry/summary", summary="Get telemetry summary")
@bearer_auth(admin_only=True)
def get_telemetry_summary():
    tenant_id = request.args.get("tenant_id")
    if not tenant_id and getattr(g, "current_user", None):
        tenant_id = str(g.current_user.tenant.id)
    return TelemetryService.summary(tenant_id or ""), 200


@internal_api.post("/me/mfa/setup", summary="Create or rotate MFA secret for current user")
@bearer_auth()
def setup_mfa():
    return MfaService.setup(g.current_user, request.get_json(silent=True) or {}), 200


@internal_api.post("/me/mfa/verify", summary="Verify MFA secret and enable MFA")
@bearer_auth()
def verify_mfa():
    return MfaService.verify(g.current_user, request.get_json(silent=True) or {}), 200


@internal_api.post("/me/mfa/disable", summary="Disable MFA for current user")
@bearer_auth()
def disable_mfa():
    return MfaService.disable(g.current_user), 200


@internal_api.post("/me/mfa/resend", summary="Resend MFA code for current user")
@bearer_auth()
def resend_mfa():
    return MfaService.resend_email_code(g.current_user), 200
