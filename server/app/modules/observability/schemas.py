from datetime import datetime

from pydantic import BaseModel


class AuditLogResponseSchema(BaseModel):
    id: str
    action: str
    actor_type: str
    status: str
    details: dict
    created_at: datetime


class TelemetrySummarySchema(BaseModel):
    tenant_id: str
    total_events: int
    login_events: int
    oauth_events: int
    failed_events: int
    top_event_types: list[dict[str, int | str]]
