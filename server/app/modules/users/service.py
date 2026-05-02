from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.core.errors import AuthenticationError, ConflictError, NotFoundError
from app.core.security import build_totp_uri, generate_one_time_code, generate_totp_secret, hash_password, hash_secret, verify_totp_code
from app.models import AuditLog, MfaChallenge, Tenant, User
from app.modules.users.schemas import MfaSetupSchema, MfaVerifySchema, UserCreateSchema, UserResponseSchema, UserUpdateSchema
from app.tasks import capture_telemetry_task, send_mfa_code_email_task, send_welcome_email_task


def serialize_user(user: User) -> UserResponseSchema:
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
        return serialize_user(user).model_dump(mode="json")

    @staticmethod
    def list(tenant_id: str | None = None) -> list[dict]:
        query = User.objects
        if tenant_id:
            tenant = Tenant.objects(id=tenant_id).first()
            if tenant is None:
                raise NotFoundError("Tenant nao encontrado.")
            query = query(tenant=tenant)
        return [serialize_user(user).model_dump(mode="json") for user in query.order_by("email")]

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
        return serialize_user(user).model_dump(mode="json")


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
