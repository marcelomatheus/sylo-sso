from __future__ import annotations

from collections import Counter

from app.core.errors import NotFoundError
from app.models import AuditLog, TelemetryLog, Tenant


class AuditLogService:
    @staticmethod
    def list(tenant_id: str | None = None) -> list[dict]:
        query = AuditLog.objects
        if tenant_id:
            tenant = Tenant.objects(id=tenant_id).first()
            if tenant is None:
                raise NotFoundError("Tenant nao encontrado.")
            query = query(tenant=tenant)
        return [
            {
                "id": str(log.id),
                "action": log.action,
                "actor_type": log.actor_type,
                "status": log.status,
                "details": log.details,
                "created_at": log.created_at.isoformat(),
            }
            for log in query.order_by("-created_at")[:100]
        ]


class TelemetryService:
    @staticmethod
    def summary(tenant_id: str) -> dict:
        tenant = Tenant.objects(id=tenant_id).first()
        if tenant is None:
            raise NotFoundError("Tenant nao encontrado.")
        logs = list(TelemetryLog.objects(tenant=tenant))
        event_counter = Counter(log.event_type for log in logs)
        top_events = [{"event_type": event_type, "count": count} for event_type, count in event_counter.most_common(5)]
        return {
            "tenant_id": tenant_id,
            "total_events": len(logs),
            "login_events": sum(1 for log in logs if log.event_type.startswith("auth.")),
            "oauth_events": sum(1 for log in logs if log.event_type.startswith("oauth.")),
            "failed_events": sum(1 for log in logs if log.metadata.get("status") == "FAILURE"),
            "top_event_types": top_events,
        }
