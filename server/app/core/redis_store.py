from __future__ import annotations

import json
import time
from threading import Lock

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings


class InMemoryRedisStore:
    def __init__(self) -> None:
        self._data: dict[str, tuple[str, float | None]] = {}
        self._lock = Lock()

    def ping(self) -> bool:
        return True

    def get(self, key: str) -> str | None:
        with self._lock:
            value = self._data.get(key)
            if value is None:
                return None
            payload, expires_at = value
            if expires_at is not None and expires_at <= time.time():
                self._data.pop(key, None)
                return None
            return payload

    def setex(self, key: str, ttl_seconds: int, value: str) -> bool:
        with self._lock:
            self._data[key] = (value, time.time() + ttl_seconds)
        return True

    def delete(self, key: str) -> int:
        with self._lock:
            existed = key in self._data
            self._data.pop(key, None)
        return int(existed)

    def incr(self, key: str) -> int:
        with self._lock:
            current = self.get(key)
            value = int(current or "0") + 1
            expires_at = self._data.get(key, ("", None))[1]
            self._data[key] = (str(value), expires_at)
            return value

    def expire(self, key: str, ttl_seconds: int) -> bool:
        with self._lock:
            current = self._data.get(key)
            if current is None:
                return False
            self._data[key] = (current[0], time.time() + ttl_seconds)
            return True


class RedisStore:
    def __init__(self) -> None:
        self._client: Redis | InMemoryRedisStore | None = None

    @property
    def client(self) -> Redis | InMemoryRedisStore:
        if self._client is None:
            settings = get_settings()
            try:
                client = Redis.from_url(settings.redis_url, decode_responses=True)
                client.ping()
                self._client = client
            except RedisError:
                self._client = InMemoryRedisStore()
        return self._client

    def get_json(self, key: str) -> dict | None:
        raw = self.client.get(key)
        return json.loads(raw) if raw else None

    def set_json(self, key: str, ttl_seconds: int, value: dict) -> None:
        self.client.setex(key, ttl_seconds, json.dumps(value))

    def is_denied(self, token_id: str) -> bool:
        return self.client.get(self._deny_key(token_id)) is not None

    def deny_token(self, token_id: str, ttl_seconds: int) -> None:
        self.client.setex(self._deny_key(token_id), ttl_seconds, "1")

    def rate_limit(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        current = self.client.incr(key)
        if current == 1:
            self.client.expire(key, window_seconds)
        return current <= max_requests, current

    @staticmethod
    def _deny_key(token_id: str) -> str:
        return f"deny:{token_id}"


redis_store = RedisStore()
