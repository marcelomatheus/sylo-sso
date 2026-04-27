from __future__ import annotations

from datetime import UTC, datetime, timedelta

import requests

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.core.notifications import (
    render_email_verification_email,
    render_mfa_code_email,
    render_password_reset_email,
    render_security_notification_email,
    render_welcome_email,
)
from app.models import TelemetryLog, Tenant


@celery_app.task(name="sylo.notifications.send_email")
def send_email_task(recipient: str, subject: str, html: str) -> dict:
    settings = get_settings()
    if not settings.mailgun_domain or not settings.mailgun_api_key:
        return {"status": "skipped", "reason": "mailgun_not_configured"}
    response = requests.post(
        f"{settings.mailgun_base_url}/{settings.mailgun_domain}/messages",
        auth=("api", settings.mailgun_api_key),
        data={
            "from": f"{settings.mail_from_name} <{settings.mail_from_address}>",
            "to": [recipient],
            "subject": subject,
            "html": html,
        },
        timeout=10,
    )
    return {"status": "sent", "status_code": response.status_code}


@celery_app.task(name="sylo.telemetry.capture")
def capture_telemetry_task(tenant_id: str, event_type: str, metadata: dict | None = None) -> dict:
    settings = get_settings()
    tenant = Tenant.objects(id=tenant_id).first()
    TelemetryLog(
        tenant=tenant,
        event_type=event_type,
        metadata=metadata or {},
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=settings.telemetry_ttl_seconds),
    ).save()
    return {"status": "stored"}


@celery_app.task(name="sylo.notifications.send_welcome_email")
def send_welcome_email_task(tenant_id: str, user_id: str, temporary_password: bool = False) -> dict:
    from app.models import User

    tenant = Tenant.objects(id=tenant_id).first()
    user = User.objects(id=user_id).first()
    if tenant is None or user is None:
        return {"status": "skipped", "reason": "tenant_or_user_missing"}
    subject, html = render_welcome_email(tenant, user, temporary_password=temporary_password)
    return send_email_task(user.email, subject, html)


@celery_app.task(name="sylo.notifications.send_security_notification")
def send_security_notification_task(tenant_id: str, user_id: str, message: str) -> dict:
    from app.models import User

    tenant = Tenant.objects(id=tenant_id).first()
    user = User.objects(id=user_id).first()
    if tenant is None or user is None:
        return {"status": "skipped", "reason": "tenant_or_user_missing"}
    subject, html = render_security_notification_email(tenant, user, message)
    return send_email_task(user.email, subject, html)


@celery_app.task(name="sylo.notifications.send_password_reset")
def send_password_reset_email_task(tenant_id: str, user_id: str, reset_url: str) -> dict:
    from app.models import User

    tenant = Tenant.objects(id=tenant_id).first()
    user = User.objects(id=user_id).first()
    if tenant is None or user is None:
        return {"status": "skipped", "reason": "tenant_or_user_missing"}
    subject, html = render_password_reset_email(tenant, user, reset_url)
    return send_email_task(user.email, subject, html)


@celery_app.task(name="sylo.notifications.send_email_verification")
def send_email_verification_task(tenant_id: str, user_id: str, verification_url: str) -> dict:
    from app.models import User

    tenant = Tenant.objects(id=tenant_id).first()
    user = User.objects(id=user_id).first()
    if tenant is None or user is None:
        return {"status": "skipped", "reason": "tenant_or_user_missing"}
    subject, html = render_email_verification_email(tenant, user, verification_url)
    return send_email_task(user.email, subject, html)


@celery_app.task(name="sylo.notifications.send_mfa_code")
def send_mfa_code_email_task(tenant_id: str, user_id: str, code: str) -> dict:
    from app.models import User

    tenant = Tenant.objects(id=tenant_id).first()
    user = User.objects(id=user_id).first()
    if tenant is None or user is None:
        return {"status": "skipped", "reason": "tenant_or_user_missing"}
    subject, html = render_mfa_code_email(tenant, user, code)
    return send_email_task(user.email, subject, html)
