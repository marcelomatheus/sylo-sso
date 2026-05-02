from flask import request
from flask_openapi3 import APIBlueprint, Tag

from app.core.guards import bearer_auth
from app.modules.access.schemas import ConsentPathSchema, RoleBindingPathSchema
from app.modules.access.service import ConsentService, RoleBindingService


internal_tag = Tag(name="Access Internal")
access_internal_api = APIBlueprint("access_internal_api", __name__, abp_tags=[internal_tag])


@access_internal_api.get("/consents", summary="List consents")
@bearer_auth(admin_only=True)
def list_consents():
    return {"items": ConsentService.list(request.args.get("tenant_id"), request.args.get("user_id"))}, 200


@access_internal_api.post("/consents/<consent_id>/revoke", summary="Revoke consent")
@bearer_auth(admin_only=True)
def revoke_consent(path: ConsentPathSchema):
    return ConsentService.revoke(path.consent_id), 200


@access_internal_api.post("/role-bindings", summary="Create role binding")
@bearer_auth(admin_only=True)
def create_role_binding():
    return RoleBindingService.create(request.get_json(silent=True) or {}), 201


@access_internal_api.get("/role-bindings", summary="List role bindings")
@bearer_auth(admin_only=True)
def list_role_bindings():
    return {
        "items": RoleBindingService.list(
            request.args.get("tenant_id"),
            request.args.get("user_id"),
            request.args.get("client_app_id"),
        )
    }, 200


@access_internal_api.patch("/role-bindings/<role_binding_id>", summary="Update role binding")
@bearer_auth(admin_only=True)
def update_role_binding(path: RoleBindingPathSchema):
    return RoleBindingService.update(path.role_binding_id, request.get_json(silent=True) or {}), 200
