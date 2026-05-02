from __future__ import annotations

import mongomock
import pytest
from mongoengine import connect, disconnect

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.core.redis_store import redis_store


@pytest.fixture(autouse=True)
def mongo_test_db():
    get_settings.cache_clear()
    settings = get_settings()
    settings.app_env = "test"
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    redis_store._client = None
    disconnect(alias="default")
    connect(
        "sylo_sso_test",
        alias="default",
        host="mongodb://localhost",
        mongo_client_class=mongomock.MongoClient,
        uuidRepresentation="standard",
    )
    yield
    disconnect(alias="default")
    get_settings.cache_clear()
