from __future__ import annotations

import mongomock
import pytest
from mongoengine import connect, disconnect

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def mongo_test_db():
    settings = get_settings()
    settings.app_env = "test"
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
