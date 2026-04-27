from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.core.errors import AuthenticationError, ConflictError
from app.core.security import decode_access_token, generate_opaque_token, hash_password, hash_secret
from app.models import AuditLog, ClientApp, Consent, EmailVerificationToken, OAuthAuthorizationCode, PasswordResetToken, Tenant, User
from app.modules.external.schemas import (
    ForgotPasswordSchema,
    PublicRegistrationSchema,
    ResendVerificationSchema,
    ResetPasswordSchema,
    VerifyEmailSchema,
)
from app.modules.internal.service import WhiteLabelService
from app.tasks import capture_telemetry_task, send_email_verification_task, send_password_reset_email_task, send_welcome_email_task


def _base_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _validate_registration_client(tenant: Tenant, client_id: str | None, redirect_uri: str | None) -> tuple[ClientApp | None, list[str]]:
    if not client_id and not redirect_uri:
        return None, []
    if not client_id or not redirect_uri:
        raise ConflictError("client_id e redirect_uri devem ser enviados juntos.")
    client_app = ClientApp.objects(client_id=client_id, tenant=tenant, status="ACTIVE").first()
    if client_app is None:
        raise AuthenticationError("Aplicacao cliente nao encontrada para este tenant.")
    if redirect_uri not in client_app.redirect_uris:
        raise ConflictError("redirect_uri nao autorizada.")
    return client_app, client_app.allowed_scopes


def _issue_email_verification_token(
    tenant: Tenant,
    user: User,
    base_url: str,
    *,
    client_app: ClientApp | None = None,
    redirect_uri: str | None = None,
    state: str | None = None,
    scopes: list[str] | None = None,
) -> None:
    EmailVerificationToken.objects(user=user, consumed_at=None).delete()
    verification_token, verification_hash = generate_opaque_token("ev")
    expires_at = _base_now() + timedelta(seconds=get_settings().email_verification_ttl_seconds)
    EmailVerificationToken(
        tenant=tenant,
        user=user,
        client_app=client_app,
        token_hash=verification_hash,
        redirect_uri=redirect_uri,
        state=state,
        scopes=scopes or [],
        expires_at=expires_at,
    ).save()
    verification_url = f"{base_url.rstrip('/')}/verify-email/{tenant.slug}/confirm?token={verification_token}"
    send_email_verification_task.delay(str(tenant.id), str(user.id), verification_url)


class TokenIntrospectionService:
    @staticmethod
    def introspect(token: str) -> dict:
        if not token:
            raise AuthenticationError("Token obrigatorio.")
        payload = decode_access_token(token)
        AuditLog(action="oauth.introspect", actor_type="API_KEY", status="SUCCESS", details={"token_id": payload["jti"]}).save()
        return {
            "active": True,
            "sub": payload["sub"],
            "aud": payload["aud"],
            "iss": payload["iss"],
            "tenant_id": payload["tenant_id"],
            "scope": payload.get("scope", ""),
            "exp": payload["exp"],
            "iat": payload["iat"],
            "checked_at": datetime.now(UTC).isoformat(),
        }


class PublicTenantService:
    @staticmethod
    def branding(tenant_slug: str) -> dict:
        return WhiteLabelService.get_by_slug(tenant_slug)


class PublicAuthService:
    @staticmethod
    def register(payload: dict, base_url: str) -> dict:
        data = PublicRegistrationSchema.model_validate(payload)
        tenant = Tenant.objects(slug=data.tenant_slug, status="ACTIVE").first()
        if tenant is None:
            raise AuthenticationError("Tenant nao encontrado.")
        client_app, default_scopes = _validate_registration_client(tenant, data.client_id, data.redirect_uri)
        requested_scopes = data.scopes or default_scopes
        if client_app and any(scope not in client_app.allowed_scopes for scope in requested_scopes):
            raise AuthenticationError("Escopo solicitado nao permitido para a aplicacao.")
        if client_app and tenant.lgpd_consent_required and not data.consent_accepted:
            raise AuthenticationError("Consentimento LGPD obrigatorio para concluir o cadastro.")
        if User.objects(tenant=tenant, email=data.email.lower()).first():
            raise AuthenticationError("Ja existe usuario com este email neste tenant.")
        user = User(
            tenant=tenant,
            email=data.email.lower(),
            name=data.name,
            password_hash=hash_password(data.password),
            role="MEMBER",
            status="ACTIVE",
            email_verified=False,
        ).save()
        AuditLog(tenant=tenant, user=user, action="public.register", actor_type="USER", status="SUCCESS").save()
        capture_telemetry_task.delay(str(tenant.id), "public.register", {"status": "SUCCESS", "user_id": str(user.id)})
        _issue_email_verification_token(
            tenant,
            user,
            base_url,
            client_app=client_app,
            redirect_uri=data.redirect_uri,
            state=data.state,
            scopes=requested_scopes,
        )
        send_welcome_email_task.delay(str(tenant.id), str(user.id), False)
        response = {
            "status": "created",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "tenant_id": str(tenant.id),
            },
        }
        if data.redirect_uri:
            response["next_step"] = {
                "type": "verify_email",
                "redirect_uri": data.redirect_uri,
                "state": data.state,
            }
        return response

    @staticmethod
    def forgot_password(payload: dict, base_url: str) -> dict:
        data = ForgotPasswordSchema.model_validate(payload)
        tenant = Tenant.objects(slug=data.tenant_slug, status="ACTIVE").first()
        if tenant is None:
            return {"status": "accepted"}
        user = User.objects(tenant=tenant, email=data.email.lower(), status="ACTIVE").first()
        if user is None:
            return {"status": "accepted"}
        reset_token, reset_hash = generate_opaque_token("pr")
        expires_at = _base_now() + timedelta(seconds=get_settings().password_reset_ttl_seconds)
        PasswordResetToken(
            tenant=tenant,
            user=user,
            token_hash=reset_hash,
            expires_at=expires_at,
        ).save()
        reset_url = f"{base_url.rstrip('/')}/reset-password/{tenant.slug}/confirm?token={reset_token}"
        send_password_reset_email_task.delay(str(tenant.id), str(user.id), reset_url)
        AuditLog(tenant=tenant, user=user, action="password.forgot", actor_type="USER", status="SUCCESS").save()
        capture_telemetry_task.delay(str(tenant.id), "password.forgot", {"status": "SUCCESS", "user_id": str(user.id)})
        return {"status": "accepted"}

    @staticmethod
    def reset_password(payload: dict) -> dict:
        data = ResetPasswordSchema.model_validate(payload)
        tenant = Tenant.objects(slug=data.tenant_slug, status="ACTIVE").first()
        if tenant is None:
            raise AuthenticationError("Tenant nao encontrado.")
        token = PasswordResetToken.objects(
            tenant=tenant,
            token_hash=hash_secret(data.token),
            consumed_at=None,
        ).first()
        now = _base_now()
        if token is None or token.expires_at <= now:
            raise AuthenticationError("Token de redefinicao invalido ou expirado.")
        user = token.user
        user.password_hash = hash_password(data.new_password)
        user.save()
        token.consumed_at = now
        token.save()
        AuditLog(tenant=tenant, user=user, action="password.reset", actor_type="USER", status="SUCCESS").save()
        capture_telemetry_task.delay(str(tenant.id), "password.reset", {"status": "SUCCESS", "user_id": str(user.id)})
        return {"status": "password_updated"}

    @staticmethod
    def verify_email(payload: dict) -> dict:
        data = VerifyEmailSchema.model_validate(payload)
        tenant = Tenant.objects(slug=data.tenant_slug, status="ACTIVE").first()
        if tenant is None:
            raise AuthenticationError("Tenant nao encontrado.")
        token = EmailVerificationToken.objects(
            tenant=tenant,
            token_hash=hash_secret(data.token),
            consumed_at=None,
        ).first()
        now = _base_now()
        if token is None or token.expires_at <= now:
            raise AuthenticationError("Token de verificacao invalido ou expirado.")
        user = token.user
        user.email_verified = True
        user.save()
        token.consumed_at = now
        token.save()
        response = {"status": "verified"}
        if token.client_app and token.redirect_uri:
            auth_code = f"ac_{generate_opaque_token('code')[0].split('_', 1)[1]}"
            OAuthAuthorizationCode(
                tenant=tenant,
                user=user,
                client_app=token.client_app,
                code_hash=hash_secret(auth_code),
                redirect_uri=token.redirect_uri,
                scopes=token.scopes or token.client_app.allowed_scopes,
                expires_at=_base_now() + timedelta(seconds=get_settings().authorization_code_ttl_seconds),
            ).save()
            Consent.objects(tenant=tenant, user=user, client_app=token.client_app).modify(
                upsert=True,
                new=True,
                set__scopes=token.scopes or token.client_app.allowed_scopes,
                set__granted_at=_base_now(),
                unset__revoked_at=1,
            )
            response["redirect_to"] = f"{token.redirect_uri}?code={auth_code}" + (f"&state={token.state}" if token.state else "")
        AuditLog(tenant=tenant, user=user, action="email.verify", actor_type="USER", status="SUCCESS").save()
        capture_telemetry_task.delay(str(tenant.id), "email.verify", {"status": "SUCCESS", "user_id": str(user.id)})
        return response

    @staticmethod
    def resend_verification(payload: dict, base_url: str) -> dict:
        data = ResendVerificationSchema.model_validate(payload)
        tenant = Tenant.objects(slug=data.tenant_slug, status="ACTIVE").first()
        if tenant is None:
            return {"status": "accepted"}
        user = User.objects(tenant=tenant, email=data.email.lower(), status="ACTIVE").first()
        if user is None or user.email_verified:
            return {"status": "accepted"}
        _issue_email_verification_token(tenant, user, base_url)
        AuditLog(tenant=tenant, user=user, action="email.resend_verification", actor_type="USER", status="SUCCESS").save()
        capture_telemetry_task.delay(str(tenant.id), "email.resend_verification", {"status": "SUCCESS", "user_id": str(user.id)})
        return {"status": "accepted"}
