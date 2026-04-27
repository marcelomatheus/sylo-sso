from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.core.errors import AuthenticationError, ConflictError, NotFoundError
from app.core.redis_store import redis_store
from app.core.security import build_totp_uri, generate_api_key, generate_client_credentials, generate_one_time_code, generate_totp_secret, hash_password, hash_secret, verify_totp_code
from collections import Counter

from app.tasks import capture_telemetry_task, send_welcome_email_task
from app.models import ApiKey, AuditLog, ClientApp, Consent, MfaChallenge, RoleBinding, TelemetryLog, Tenant, User
from app.modules.internal.schemas import (
    BootstrapSchema,
    ApiKeyCreateSchema,
    ApiKeyResponseSchema,
    ApiKeySecretResponseSchema,
    ClientAppCreateSchema,
    ClientAppResponseSchema,
    ClientAppUpdateSchema,
    MfaSetupSchema,
    MfaVerifySchema,
    RoleBindingCreateSchema,
    RoleBindingResponseSchema,
    RoleBindingUpdateSchema,
    TenantCreateSchema,
    TenantResponseSchema,
    TenantUpdateSchema,
    UserCreateSchema,
    UserResponseSchema,
    UserUpdateSchema,
)
from app.tasks import send_mfa_code_email_task


def _serialize_tenant(tenant: Tenant) -> TenantResponseSchema:
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


def _serialize_user(user: User) -> UserResponseSchema:
    return UserResponseSchema(
        id=str(user.id),
        tenant_id=str(user.tenant.id),
        email=user.email,
        name=user.name,
        role=user.role,
        status=user.status,
        email_verified=user.email_verified,
        mfa_enabled=user.mfa_enabled,
        mfa_method=user.mfa_method,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _serialize_client_app(client_app: ClientApp) -> ClientAppResponseSchema:
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


def _serialize_api_key(api_key: ApiKey) -> ApiKeyResponseSchema:
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


def _serialize_role_binding(role_binding: RoleBinding) -> RoleBindingResponseSchema:
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


class TenantService:
    @staticmethod
    def create(payload: dict) -> dict:
        data = TenantCreateSchema.model_validate(payload)
        if Tenant.objects(slug=data.slug).first():
            raise ConflictError("Slug do tenant ja esta em uso.")
        branding = data.branding.model_dump() if data.branding else {"support_email": data.contact_email}
        tenant = Tenant(**data.model_dump(exclude={"branding"}), branding=branding).save()
        return _serialize_tenant(tenant).model_dump(mode="json")

    @staticmethod
    def bootstrap(payload: dict) -> dict:
        from app.modules.oauth.service import OAuthService

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
            user_response = _serialize_user(admin_user).model_dump(mode="json")
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
        return [_serialize_tenant(tenant).model_dump(mode="json") for tenant in Tenant.objects.order_by("name")]

    @staticmethod
    def get(tenant_id: str) -> dict:
        tenant = Tenant.objects(id=tenant_id).first()
        if tenant is None:
            raise NotFoundError("Tenant nao encontrado.")
        return _serialize_tenant(tenant).model_dump(mode="json")

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
        return _serialize_tenant(tenant).model_dump(mode="json")


class UserService:
    @staticmethod
    def create(payload: dict) -> dict:
        data = UserCreateSchema.model_validate(payload)
        tenant = Tenant.objects(id=data.tenant_id, status="ACTIVE").first()
        if tenant is None:
            raise NotFoundError("Tenant ativo nao encontrado.")
        if User.objects(tenant=tenant, email=data.email.lower()).first():
            raise ConflictError("Ja existe usuario com este email neste tenant.")
        user = User(
            tenant=tenant,
            email=data.email.lower(),
            name=data.name,
            password_hash=hash_password(data.password),
            role=data.role,
            status=data.status,
        ).save()
        AuditLog(tenant=tenant, user=user, action="user.created", actor_type="USER", status="SUCCESS").save()
        capture_telemetry_task.delay(str(tenant.id), "user.created", {"status": "SUCCESS", "user_id": str(user.id)})
        send_welcome_email_task.delay(str(tenant.id), str(user.id), data.status == "INVITED")
        return _serialize_user(user).model_dump(mode="json")

    @staticmethod
    def list(tenant_id: str | None = None) -> list[dict]:
        query = User.objects
        if tenant_id:
            tenant = Tenant.objects(id=tenant_id).first()
            if tenant is None:
                raise NotFoundError("Tenant nao encontrado.")
            query = query(tenant=tenant)
        return [_serialize_user(user).model_dump(mode="json") for user in query.order_by("email")]

    @staticmethod
    def update(user_id: str, payload: dict) -> dict:
        user = User.objects(id=user_id).first()
        if user is None:
            raise NotFoundError("Usuario nao encontrado.")
        data = UserUpdateSchema.model_validate(payload)
        for field, value in data.model_dump(exclude_none=True).items():
            if field == "password":
                user.password_hash = hash_password(value)
            else:
                setattr(user, field, value)
        user.save()
        return _serialize_user(user).model_dump(mode="json")


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
        payload = _serialize_client_app(client_app).model_dump(mode="json")
        if not data.is_public:
            payload["client_secret"] = client_secret
        return payload

    @staticmethod
    def list(tenant_id: str | None = None) -> list[dict]:
        query = ClientApp.objects
        if tenant_id:
            tenant = Tenant.objects(id=tenant_id).first()
            if tenant is None:
                raise NotFoundError("Tenant nao encontrado.")
            query = query(tenant=tenant)
        return [_serialize_client_app(client_app).model_dump(mode="json") for client_app in query.order_by("name")]

    @staticmethod
    def update(client_app_id: str, payload: dict) -> dict:
        client_app = ClientApp.objects(id=client_app_id).first()
        if client_app is None:
            raise NotFoundError("Aplicacao nao encontrada.")
        data = ClientAppUpdateSchema.model_validate(payload)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(client_app, field, value)
        client_app.save()
        return _serialize_client_app(client_app).model_dump(mode="json")


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
        payload = ApiKeySecretResponseSchema(
            **_serialize_api_key(api_key).model_dump(),
            secret=secret,
        )
        return payload.model_dump(mode="json")

    @staticmethod
    def revoke(api_key_id: str) -> dict:
        api_key = ApiKey.objects(id=api_key_id).first()
        if api_key is None:
            raise NotFoundError("API Key nao encontrada.")
        api_key.status = "REVOKED"
        api_key.save()
        capture_telemetry_task.delay(str(api_key.tenant.id), "api_key.revoked", {"status": "SUCCESS", "api_key_id": str(api_key.id)})
        return _serialize_api_key(api_key).model_dump(mode="json")

    @staticmethod
    def list(tenant_id: str | None = None) -> list[dict]:
        query = ApiKey.objects
        if tenant_id:
            tenant = Tenant.objects(id=tenant_id).first()
            if tenant is None:
                raise NotFoundError("Tenant nao encontrado.")
            query = query(tenant=tenant)
        return [_serialize_api_key(api_key).model_dump(mode="json") for api_key in query.order_by("-created_at")]

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
        payload = ApiKeySecretResponseSchema(**_serialize_api_key(api_key).model_dump(), secret=secret)
        return payload.model_dump(mode="json")


class AuditLogService:
    @staticmethod
    def list(tenant_id: str | None = None) -> list[dict]:
        query = AuditLog.objects
        if tenant_id:
            tenant = Tenant.objects(id=tenant_id).first()
            if tenant is None:
                raise NotFoundError("Tenant nao encontrado.")
            query = query(tenant=tenant)
        return [
            {
                "id": str(log.id),
                "action": log.action,
                "actor_type": log.actor_type,
                "status": log.status,
                "details": log.details,
                "created_at": log.created_at.isoformat(),
            }
            for log in query.order_by("-created_at")[:100]
        ]


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
        return _serialize_role_binding(role_binding).model_dump(mode="json")

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
        return [_serialize_role_binding(role_binding).model_dump(mode="json") for role_binding in query.order_by("-updated_at")]

    @staticmethod
    def update(role_binding_id: str, payload: dict) -> dict:
        role_binding = RoleBinding.objects(id=role_binding_id).first()
        if role_binding is None:
            raise NotFoundError("Role binding nao encontrado.")
        data = RoleBindingUpdateSchema.model_validate(payload)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(role_binding, field, value)
        role_binding.save()
        return _serialize_role_binding(role_binding).model_dump(mode="json")


class MfaService:
    @staticmethod
    def _issue_email_code(user: User) -> str:
        code = generate_one_time_code()
        MfaChallenge.objects(user=user, consumed_at=None).delete()
        MfaChallenge(
            tenant=user.tenant,
            user=user,
            code_hash=hash_secret(code),
            method="EMAIL",
            expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=get_settings().mfa_email_code_ttl_seconds),
        ).save()
        send_mfa_code_email_task.delay(str(user.tenant.id), str(user.id), code)
        return code

    @staticmethod
    def setup(user: User, payload: dict | None = None) -> dict:
        data = MfaSetupSchema.model_validate(payload or {})
        user.mfa_enabled = False
        user.mfa_method = data.method
        if data.method == "TOTP":
            secret = generate_totp_secret()
            user.mfa_secret = secret
            user.save()
            return {
                "secret": secret,
                "otpauth_uri": build_totp_uri(secret, user.email, str(user.tenant.slug)),
                "already_enabled": False,
                "method": "TOTP",
            }

        user.mfa_secret = None
        user.save()
        MfaService._issue_email_code(user)
        return {
            "secret": "",
            "otpauth_uri": "",
            "already_enabled": False,
            "method": "EMAIL",
            "delivery": "email",
        }

    @staticmethod
    def verify(user: User, payload: dict) -> dict:
        data = MfaVerifySchema.model_validate(payload)
        if user.mfa_method == "EMAIL":
            challenge = MfaChallenge.objects(
                user=user,
                method="EMAIL",
                code_hash=hash_secret(data.code),
                consumed_at=None,
            ).first()
            now = datetime.now(UTC).replace(tzinfo=None)
            if challenge is None or challenge.expires_at <= now:
                raise AuthenticationError("Codigo MFA invalido ou expirado.")
            challenge.consumed_at = now
            challenge.save()
        else:
            if not user.mfa_secret:
                raise AuthenticationError("Configure o MFA antes de validar o codigo.")
            if not verify_totp_code(user.mfa_secret, data.code):
                raise AuthenticationError("Codigo MFA invalido.")
        user.mfa_enabled = True
        user.save()
        AuditLog(tenant=user.tenant, user=user, action="mfa.enabled", actor_type="USER", status="SUCCESS").save()
        capture_telemetry_task.delay(str(user.tenant.id), "mfa.enabled", {"status": "SUCCESS", "user_id": str(user.id)})
        return {"status": "enabled", "method": user.mfa_method}

    @staticmethod
    def resend_email_code(user: User) -> dict:
        if user.mfa_method != "EMAIL":
            raise AuthenticationError("Reenvio disponivel apenas para MFA por e-mail.")
        MfaService._issue_email_code(user)
        return {"status": "sent"}

    @staticmethod
    def disable(user: User) -> dict:
        user.mfa_secret = None
        user.mfa_enabled = False
        user.mfa_method = None
        user.save()
        MfaChallenge.objects(user=user, consumed_at=None).delete()
        AuditLog(tenant=user.tenant, user=user, action="mfa.disabled", actor_type="USER", status="SUCCESS").save()
        capture_telemetry_task.delay(str(user.tenant.id), "mfa.disabled", {"status": "SUCCESS", "user_id": str(user.id)})
        return {"status": "disabled"}


class TelemetryService:
    @staticmethod
    def summary(tenant_id: str) -> dict:
        tenant = Tenant.objects(id=tenant_id).first()
        if tenant is None:
            raise NotFoundError("Tenant nao encontrado.")
        logs = list(TelemetryLog.objects(tenant=tenant))
        event_counter = Counter(log.event_type for log in logs)
        top_events = [{"event_type": event_type, "count": count} for event_type, count in event_counter.most_common(5)]
        return {
            "tenant_id": tenant_id,
            "total_events": len(logs),
            "login_events": sum(1 for log in logs if log.event_type.startswith("auth.")),
            "oauth_events": sum(1 for log in logs if log.event_type.startswith("oauth.")),
            "failed_events": sum(1 for log in logs if log.metadata.get("status") == "FAILURE"),
            "top_event_types": top_events,
        }
