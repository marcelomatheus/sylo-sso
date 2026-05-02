from __future__ import annotations

from datetime import UTC, datetime

from app.core.errors import ConflictError, NotFoundError
from app.models import AuditLog, ClientApp, Consent, RoleBinding, Tenant, User
from app.modules.access.schemas import RoleBindingCreateSchema, RoleBindingResponseSchema, RoleBindingUpdateSchema
from app.tasks import capture_telemetry_task


def serialize_role_binding(role_binding: RoleBinding) -> RoleBindingResponseSchema:
    return RoleBindingResponseSchema(
        id=str(role_binding.id),
        tenant_id=str(role_binding.tenant.id),
        user_id=str(role_binding.user.id),
        client_app_id=str(role_binding.client_app.id),
        roles=role_binding.roles,
        scopes=role_binding.scopes,
        status=role_binding.status,
        created_at=role_binding.created_at,
        updated_at=role_binding.updated_at,
    )


class ConsentService:
    @staticmethod
    def list(tenant_id: str | None = None, user_id: str | None = None) -> list[dict]:
        query = Consent.objects
        if tenant_id:
            tenant = Tenant.objects(id=tenant_id).first()
            if tenant is None:
                raise NotFoundError("Tenant nao encontrado.")
            query = query(tenant=tenant)
        if user_id:
            user = User.objects(id=user_id).first()
            if user is None:
                raise NotFoundError("Usuario nao encontrado.")
            query = query(user=user)
        return [
            {
                "id": str(consent.id),
                "tenant_id": str(consent.tenant.id),
                "user_id": str(consent.user.id),
                "client_app_id": str(consent.client_app.id),
                "scopes": consent.scopes,
                "granted_at": consent.granted_at.isoformat(),
                "revoked_at": consent.revoked_at.isoformat() if consent.revoked_at else None,
            }
            for consent in query.order_by("-updated_at")
        ]

    @staticmethod
    def revoke(consent_id: str) -> dict:
        consent = Consent.objects(id=consent_id).first()
        if consent is None:
            raise NotFoundError("Consentimento nao encontrado.")
        consent.revoked_at = datetime.now(UTC).replace(tzinfo=None)
        consent.save()
        AuditLog(
            tenant=consent.tenant,
            user=consent.user,
            client_app=consent.client_app,
            action="consent.revoked",
            actor_type="USER",
            status="SUCCESS",
        ).save()
        capture_telemetry_task.delay(str(consent.tenant.id), "consent.revoked", {"status": "SUCCESS", "consent_id": str(consent.id)})
        return {
            "id": str(consent.id),
            "tenant_id": str(consent.tenant.id),
            "user_id": str(consent.user.id),
            "client_app_id": str(consent.client_app.id),
            "scopes": consent.scopes,
            "granted_at": consent.granted_at.isoformat(),
            "revoked_at": consent.revoked_at.isoformat() if consent.revoked_at else None,
        }


class RoleBindingService:
    @staticmethod
    def create(payload: dict) -> dict:
        data = RoleBindingCreateSchema.model_validate(payload)
        tenant = Tenant.objects(id=data.tenant_id).first()
        if tenant is None:
            raise NotFoundError("Tenant nao encontrado.")
        user = User.objects(id=data.user_id, tenant=tenant).first()
        if user is None:
            raise NotFoundError("Usuario nao encontrado neste tenant.")
        client_app = ClientApp.objects(id=data.client_app_id, tenant=tenant).first()
        if client_app is None:
            raise NotFoundError("Aplicacao nao encontrada neste tenant.")
        role_binding = RoleBinding.objects(tenant=tenant, user=user, client_app=client_app).first()
        if role_binding is not None:
            raise ConflictError("Role binding ja existe para este usuario e aplicacao.")
        role_binding = RoleBinding(
            tenant=tenant,
            user=user,
            client_app=client_app,
            roles=data.roles,
            scopes=data.scopes,
            status=data.status,
        ).save()
        return serialize_role_binding(role_binding).model_dump(mode="json")

    @staticmethod
    def list(tenant_id: str | None = None, user_id: str | None = None, client_app_id: str | None = None) -> list[dict]:
        query = RoleBinding.objects
        if tenant_id:
            tenant = Tenant.objects(id=tenant_id).first()
            if tenant is None:
                raise NotFoundError("Tenant nao encontrado.")
            query = query(tenant=tenant)
        if user_id:
            user = User.objects(id=user_id).first()
            if user is None:
                raise NotFoundError("Usuario nao encontrado.")
            query = query(user=user)
        if client_app_id:
            client_app = ClientApp.objects(id=client_app_id).first()
            if client_app is None:
                raise NotFoundError("Aplicacao nao encontrada.")
            query = query(client_app=client_app)
        return [serialize_role_binding(role_binding).model_dump(mode="json") for role_binding in query.order_by("-updated_at")]

    @staticmethod
    def update(role_binding_id: str, payload: dict) -> dict:
        role_binding = RoleBinding.objects(id=role_binding_id).first()
        if role_binding is None:
            raise NotFoundError("Role binding nao encontrado.")
        data = RoleBindingUpdateSchema.model_validate(payload)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(role_binding, field, value)
        role_binding.save()
        return serialize_role_binding(role_binding).model_dump(mode="json")
