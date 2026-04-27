from flask import Request

from app.core.config import get_settings
from app.core.errors import RateLimitError
from app.core.redis_store import redis_store


def enforce_rate_limit(request: Request, prefix: str, tenant_id: str | None = None, client_id: str | None = None) -> None:
    settings = get_settings()
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
    key = f"rl:{prefix}:{tenant_id or 'public'}:{client_id or 'na'}:{ip}"
    allowed, current = redis_store.rate_limit(key, settings.rate_limit_max_requests, settings.rate_limit_window_seconds)
    if not allowed:
        raise RateLimitError(details={"bucket": key, "current": current})
