from flask import g, request
from flask_openapi3 import APIBlueprint, Tag

from app.core.guards import bearer_auth
from app.modules.observability.service import AuditLogService, TelemetryService


internal_tag = Tag(name="Observability Internal")
observability_internal_api = APIBlueprint("observability_internal_api", __name__, abp_tags=[internal_tag])


@observability_internal_api.get("/audit-logs", summary="List audit logs")
@bearer_auth(admin_only=True)
def list_audit_logs():
    return {"items": AuditLogService.list(request.args.get("tenant_id"))}, 200


@observability_internal_api.get("/telemetry/summary", summary="Get telemetry summary")
@bearer_auth(admin_only=True)
def get_telemetry_summary():
    tenant_id = request.args.get("tenant_id")
    if not tenant_id and getattr(g, "current_user", None):
        tenant_id = str(g.current_user.tenant.id)
    return TelemetryService.summary(tenant_id or ""), 200
