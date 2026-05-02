from __future__ import annotations

from app.core.errors import ConflictError, NotFoundError
from app.core.redis_store import redis_store
from app.models import Tenant, User
from app.modules.tenants.schemas import BootstrapSchema, TenantCreateSchema, TenantResponseSchema, TenantUpdateSchema
from app.modules.users.service import UserService, serialize_user


def serialize_tenant(tenant: Tenant) -> TenantResponseSchema:
    return TenantResponseSchema(
        id=str(tenant.id),
        name=tenant.name,
        slug=tenant.slug,
        contact_email=tenant.contact_email,
        plan=tenant.plan,
        status=tenant.status,
        lgpd_consent_required=tenant.lgpd_consent_required,
        branding=tenant.branding.to_mongo().to_dict() if tenant.branding else {},
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


class TenantService:
    @staticmethod
    def create(payload: dict) -> dict:
        data = TenantCreateSchema.model_validate(payload)
        if Tenant.objects(slug=data.slug).first():
            raise ConflictError("Slug do tenant ja esta em uso.")
        branding = data.branding.model_dump() if data.branding else {"support_email": data.contact_email}
        tenant = Tenant(**data.model_dump(exclude={"branding"}), branding=branding).save()
        return serialize_tenant(tenant).model_dump(mode="json")

    @staticmethod
    def bootstrap(payload: dict) -> dict:
        from app.modules.auth.service import OAuthService

        if Tenant.objects.count() > 0 or User.objects.count() > 0:
            raise ConflictError("Bootstrap inicial ja foi executado.")
        data = BootstrapSchema.model_validate(payload)
        tenant_response = TenantService.create(data.tenant.model_dump(mode="python"))
        user_response = UserService.create(
            {
                "tenant_id": tenant_response["id"],
                "email": data.admin_email,
                "name": data.admin_name,
                "password": data.admin_password,
                "role": "ADMIN",
                "status": "ACTIVE",
            }
        )
        admin_user = User.objects(id=user_response["id"]).first()
        if admin_user is not None:
            admin_user.email_verified = True
            admin_user.save()
            user_response = serialize_user(admin_user).model_dump(mode="json")
        auth_response = OAuthService.login(
            {
                "tenant_slug": tenant_response["slug"],
                "email": data.admin_email,
                "password": data.admin_password,
            }
        )
        return {"tenant": tenant_response, "admin_user": user_response, "session": auth_response}

    @staticmethod
    def list() -> list[dict]:
        return [serialize_tenant(tenant).model_dump(mode="json") for tenant in Tenant.objects.order_by("name")]

    @staticmethod
    def get(tenant_id: str) -> dict:
        tenant = Tenant.objects(id=tenant_id).first()
        if tenant is None:
            raise NotFoundError("Tenant nao encontrado.")
        return serialize_tenant(tenant).model_dump(mode="json")

    @staticmethod
    def update(tenant_id: str, payload: dict) -> dict:
        tenant = Tenant.objects(id=tenant_id).first()
        if tenant is None:
            raise NotFoundError("Tenant nao encontrado.")
        data = TenantUpdateSchema.model_validate(payload)
        for field, value in data.model_dump(exclude_none=True).items():
            if field == "branding" and value:
                tenant.branding = value
            else:
                setattr(tenant, field, value)
        tenant.save()
        redis_store.client.delete(f"branding:{tenant.slug}")
        return serialize_tenant(tenant).model_dump(mode="json")


class WhiteLabelService:
    @staticmethod
    def get_by_slug(tenant_slug: str) -> dict:
        cache_key = f"branding:{tenant_slug}"
        cached = redis_store.get_json(cache_key)
        if cached:
            return cached
        tenant = Tenant.objects(slug=tenant_slug, status="ACTIVE").first()
        if tenant is None:
            raise NotFoundError("Tenant nao encontrado.")
        payload = {
            "tenant_name": tenant.name,
            "tenant_slug": tenant.slug,
            "lgpd_consent_required": tenant.lgpd_consent_required,
            "branding": tenant.branding.to_mongo().to_dict() if tenant.branding else {},
        }
        redis_store.set_json(cache_key, 3600, payload)
        return payload
