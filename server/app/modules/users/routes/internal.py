from flask import g, request
from flask_openapi3 import APIBlueprint, Tag

from app.core.guards import bearer_auth
from app.modules.users.schemas import UserPathSchema
from app.modules.users.service import MfaService, UserService


internal_tag = Tag(name="Users Internal")
users_internal_api = APIBlueprint("users_internal_api", __name__, abp_tags=[internal_tag])


@users_internal_api.post("/", summary="Create user")
@bearer_auth(admin_only=True)
def create_user():
    return UserService.create(request.get_json(silent=True) or {}), 201


@users_internal_api.get("/", summary="List users")
@bearer_auth(admin_only=True)
def list_users():
    return {"items": UserService.list(request.args.get("tenant_id"))}, 200


@users_internal_api.patch("/<user_id>", summary="Update user")
@bearer_auth(admin_only=True)
def update_user(path: UserPathSchema):
    return UserService.update(path.user_id, request.get_json(silent=True) or {}), 200


@users_internal_api.post("/me/mfa/setup", summary="Create or rotate MFA secret for current user")
@bearer_auth()
def setup_mfa():
    return MfaService.setup(g.current_user, request.get_json(silent=True) or {}), 200


@users_internal_api.post("/me/mfa/verify", summary="Verify MFA secret and enable MFA")
@bearer_auth()
def verify_mfa():
    return MfaService.verify(g.current_user, request.get_json(silent=True) or {}), 200


@users_internal_api.post("/me/mfa/disable", summary="Disable MFA for current user")
@bearer_auth()
def disable_mfa():
    return MfaService.disable(g.current_user), 200


@users_internal_api.post("/me/mfa/resend", summary="Resend MFA code for current user")
@bearer_auth()
def resend_mfa():
    return MfaService.resend_email_code(g.current_user), 200
