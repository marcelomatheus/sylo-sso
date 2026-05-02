from flask import request
from flask_openapi3 import APIBlueprint, Tag

from app.core.guards import bearer_auth
from app.modules.applications.schemas import ApiKeyPathSchema, ClientAppPathSchema
from app.modules.applications.service import ApiKeyService, ClientAppService


internal_tag = Tag(name="Applications Internal")
applications_internal_api = APIBlueprint("applications_internal_api", __name__, abp_tags=[internal_tag])


@applications_internal_api.post("/", summary="Create client app")
@bearer_auth(admin_only=True)
def create_client_app():
    return ClientAppService.create(request.get_json(silent=True) or {}), 201


@applications_internal_api.get("/", summary="List client apps")
@bearer_auth(admin_only=True)
def list_client_apps():
    return {"items": ClientAppService.list(request.args.get("tenant_id"))}, 200


@applications_internal_api.patch("/<client_app_id>", summary="Update client app")
@bearer_auth(admin_only=True)
def update_client_app(path: ClientAppPathSchema):
    return ClientAppService.update(path.client_app_id, request.get_json(silent=True) or {}), 200


@applications_internal_api.post("/api-keys", summary="Create API key")
@bearer_auth(admin_only=True)
def create_api_key():
    return ApiKeyService.create(request.get_json(silent=True) or {}), 201


@applications_internal_api.get("/api-keys", summary="List API keys")
@bearer_auth(admin_only=True)
def list_api_keys():
    return {"items": ApiKeyService.list(request.args.get("tenant_id"))}, 200


@applications_internal_api.post("/api-keys/<api_key_id>/revoke", summary="Revoke API key")
@bearer_auth(admin_only=True)
def revoke_api_key(path: ApiKeyPathSchema):
    return ApiKeyService.revoke(path.api_key_id), 200


@applications_internal_api.post("/api-keys/<api_key_id>/rotate", summary="Rotate API key")
@bearer_auth(admin_only=True)
def rotate_api_key(path: ApiKeyPathSchema):
    return ApiKeyService.rotate(path.api_key_id), 200
