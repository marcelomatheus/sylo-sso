from flask import request
from flask_openapi3 import APIBlueprint, Tag

from app.core.guards import bearer_auth
from app.modules.tenants.schemas import TenantPathSchema, TenantSlugPathSchema
from app.modules.tenants.service import TenantService, WhiteLabelService


internal_tag = Tag(name="Tenants Internal")
tenants_internal_api = APIBlueprint("tenants_internal_api", __name__, abp_tags=[internal_tag])


@tenants_internal_api.post("/bootstrap", summary="Bootstrap first tenant and admin")
def bootstrap():
    return TenantService.bootstrap(request.get_json(silent=True) or {}), 201


@tenants_internal_api.post("/", summary="Create tenant")
@bearer_auth(admin_only=True)
def create_tenant():
    return TenantService.create(request.get_json(silent=True) or {}), 201


@tenants_internal_api.get("/", summary="List tenants")
@bearer_auth(admin_only=True)
def list_tenants():
    return {"items": TenantService.list()}, 200


@tenants_internal_api.get("/<tenant_id>", summary="Get tenant")
@bearer_auth(admin_only=True)
def get_tenant(path: TenantPathSchema):
    return TenantService.get(path.tenant_id), 200


@tenants_internal_api.patch("/<tenant_id>", summary="Update tenant")
@bearer_auth(admin_only=True)
def update_tenant(path: TenantPathSchema):
    return TenantService.update(path.tenant_id, request.get_json(silent=True) or {}), 200


@tenants_internal_api.get("/branding/<tenant_slug>", summary="Get tenant branding")
@bearer_auth(admin_only=True)
def get_tenant_branding(path: TenantSlugPathSchema):
    return WhiteLabelService.get_by_slug(path.tenant_slug), 200
