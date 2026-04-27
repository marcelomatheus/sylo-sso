from celery import Celery

from app.core.config import get_settings


def create_celery() -> Celery:
    settings = get_settings()
    broker = settings.celery_broker_url or settings.redis_url
    backend = settings.celery_result_backend or settings.redis_url
    celery = Celery("sylo_sso", broker=broker, backend=backend)
    celery.conf.task_always_eager = settings.app_env == "test"
    celery.conf.task_ignore_result = True
    return celery


celery_app = create_celery()
