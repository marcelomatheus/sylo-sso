from __future__ import annotations

from app.core.errors import NotFoundError
from app.core.security import generate_api_key, generate_client_credentials, hash_password
from app.models import ApiKey, ClientApp, Tenant
from app.modules.applications.schemas import ApiKeyCreateSchema, ApiKeyResponseSchema, ApiKeySecretResponseSchema, ClientAppCreateSchema, ClientAppResponseSchema, ClientAppUpdateSchema
from app.tasks import capture_telemetry_task


def serialize_client_app(client_app: ClientApp) -> ClientAppResponseSchema:
    return ClientAppResponseSchema(
        id=str(client_app.id),
        tenant_id=str(client_app.tenant.id),
        name=client_app.name,
        description=client_app.description,
        client_id=client_app.client_id,
        is_public=client_app.is_public,
        redirect_uris=client_app.redirect_uris,
        allowed_scopes=client_app.allowed_scopes,
        status=client_app.status,
        created_at=client_app.created_at,
        updated_at=client_app.updated_at,
    )


def serialize_api_key(api_key: ApiKey) -> ApiKeyResponseSchema:
    return ApiKeyResponseSchema(
        id=str(api_key.id),
        tenant_id=str(api_key.tenant.id),
        client_app_id=str(api_key.client_app.id) if api_key.client_app else None,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        status=api_key.status,
        created_at=api_key.created_at,
        updated_at=api_key.updated_at,
    )


class ClientAppService:
    @staticmethod
    def create(payload: dict) -> dict:
        data = ClientAppCreateSchema.model_validate(payload)
        tenant = Tenant.objects(id=data.tenant_id, status="ACTIVE").first()
        if tenant is None:
            raise NotFoundError("Tenant ativo nao encontrado.")
        client_id, client_secret = generate_client_credentials()
        client_app = ClientApp(
            tenant=tenant,
            name=data.name,
            description=data.description,
            client_id=client_id,
            client_secret_hash=None if data.is_public else hash_password(client_secret),
            is_public=data.is_public,
            redirect_uris=data.redirect_uris,
            allowed_scopes=data.allowed_scopes,
        ).save()
        capture_telemetry_task.delay(str(tenant.id), "client_app.created", {"status": "SUCCESS", "client_app_id": str(client_app.id)})
        response_payload = serialize_client_app(client_app).model_dump(mode="json")
        if not data.is_public:
            response_payload["client_secret"] = client_secret
        return response_payload

    @staticmethod
    def list(tenant_id: str | None = None) -> list[dict]:
        query = ClientApp.objects
        if tenant_id:
            tenant = Tenant.objects(id=tenant_id).first()
            if tenant is None:
                raise NotFoundError("Tenant nao encontrado.")
            query = query(tenant=tenant)
        return [serialize_client_app(client_app).model_dump(mode="json") for client_app in query.order_by("name")]

    @staticmethod
    def update(client_app_id: str, payload: dict) -> dict:
        client_app = ClientApp.objects(id=client_app_id).first()
        if client_app is None:
            raise NotFoundError("Aplicacao nao encontrada.")
        data = ClientAppUpdateSchema.model_validate(payload)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(client_app, field, value)
        client_app.save()
        return serialize_client_app(client_app).model_dump(mode="json")


class ApiKeyService:
    @staticmethod
    def create(payload: dict) -> dict:
        data = ApiKeyCreateSchema.model_validate(payload)
        tenant = Tenant.objects(id=data.tenant_id, status="ACTIVE").first()
        if tenant is None:
            raise NotFoundError("Tenant ativo nao encontrado.")
        client_app = None
        if data.client_app_id:
            client_app = ClientApp.objects(id=data.client_app_id, tenant=tenant).first()
            if client_app is None:
                raise NotFoundError("Aplicacao nao encontrada para este tenant.")
        secret, prefix, key_hash = generate_api_key()
        api_key = ApiKey(
            tenant=tenant,
            client_app=client_app,
            name=data.name,
            key_prefix=prefix,
            key_hash=key_hash,
            scopes=data.scopes,
        ).save()
        capture_telemetry_task.delay(str(tenant.id), "api_key.created", {"status": "SUCCESS", "api_key_id": str(api_key.id)})
        payload = ApiKeySecretResponseSchema(**serialize_api_key(api_key).model_dump(), secret=secret)
        return payload.model_dump(mode="json")

    @staticmethod
    def revoke(api_key_id: str) -> dict:
        api_key = ApiKey.objects(id=api_key_id).first()
        if api_key is None:
            raise NotFoundError("API Key nao encontrada.")
        api_key.status = "REVOKED"
        api_key.save()
        capture_telemetry_task.delay(str(api_key.tenant.id), "api_key.revoked", {"status": "SUCCESS", "api_key_id": str(api_key.id)})
        return serialize_api_key(api_key).model_dump(mode="json")

    @staticmethod
    def list(tenant_id: str | None = None) -> list[dict]:
        query = ApiKey.objects
        if tenant_id:
            tenant = Tenant.objects(id=tenant_id).first()
            if tenant is None:
                raise NotFoundError("Tenant nao encontrado.")
            query = query(tenant=tenant)
        return [serialize_api_key(api_key).model_dump(mode="json") for api_key in query.order_by("-created_at")]

    @staticmethod
    def rotate(api_key_id: str) -> dict:
        api_key = ApiKey.objects(id=api_key_id).first()
        if api_key is None:
            raise NotFoundError("API Key nao encontrada.")
        secret, prefix, key_hash = generate_api_key()
        api_key.key_prefix = prefix
        api_key.key_hash = key_hash
        api_key.status = "ACTIVE"
        api_key.save()
        capture_telemetry_task.delay(str(api_key.tenant.id), "api_key.rotated", {"status": "SUCCESS", "api_key_id": str(api_key.id)})
        payload = ApiKeySecretResponseSchema(**serialize_api_key(api_key).model_dump(), secret=secret)
        return payload.model_dump(mode="json")
