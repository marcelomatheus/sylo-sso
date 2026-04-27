from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.core.errors import AuthenticationError, ConflictError, NotFoundError
from app.core.security import decode_access_token, generate_one_time_code, generate_opaque_token, hash_secret, issue_access_token, revoke_access_token, verify_totp_code, verify_password
from app.models import AuditLog, AuthSession, ClientApp, Consent, MfaChallenge, OAuthAuthorizationCode, RoleBinding, Tenant, User
from app.modules.oauth.schemas import AuthorizeSchema, LoginSchema, RevokeSchema, TokenSchema
from app.tasks import capture_telemetry_task, send_mfa_code_email_task, send_security_notification_task


def _authenticate_user(tenant_slug: str, email: str, password: str) -> tuple[Tenant, User]:
    tenant = Tenant.objects(slug=tenant_slug, status="ACTIVE").first()
    if tenant is None:
        raise NotFoundError("Tenant nao encontrado.")
    user = User.objects(tenant=tenant, email=email.lower(), status="ACTIVE").first()
    if user is None or not verify_password(password, user.password_hash):
        AuditLog(tenant=tenant, action="auth.login", actor_type="USER", status="FAILURE").save()
        capture_telemetry_task.delay(str(tenant.id), "auth.login", {"status": "FAILURE", "email": email.lower()})
        raise AuthenticationError("Credenciais invalidas.")
    if user.role == "MEMBER" and not user.email_verified:
        AuditLog(tenant=tenant, user=user, action="auth.login", actor_type="USER", status="FAILURE").save()
        capture_telemetry_task.delay(str(tenant.id), "auth.login", {"status": "FAILURE", "user_id": str(user.id), "reason": "email_not_verified"})
        raise AuthenticationError("Confirme seu e-mail antes de continuar.")
    return tenant, user


def _utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _validate_client(client_id: str, redirect_uri: str) -> ClientApp:
    client_app = ClientApp.objects(client_id=client_id, status="ACTIVE").first()
    if client_app is None:
        raise NotFoundError("Aplicacao cliente nao encontrada.")
    if redirect_uri not in client_app.redirect_uris:
        raise ConflictError("redirect_uri nao autorizada.")
    return client_app


def _validate_client_secret(client_app: ClientApp, client_secret: str | None) -> None:
    if client_app.is_public:
        return
    if not client_secret or not client_app.client_secret_hash or not verify_password(client_secret, client_app.client_secret_hash):
        raise AuthenticationError("Client secret invalido.")


def _validate_pkce(code_verifier: str | None, auth_code: OAuthAuthorizationCode) -> None:
    if not auth_code.code_challenge:
        return
    if not code_verifier:
        raise AuthenticationError("code_verifier obrigatorio.")
    if auth_code.code_challenge_method == "S256":
        digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        computed = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    else:
        computed = code_verifier
    if computed != auth_code.code_challenge:
        raise AuthenticationError("Falha na validacao PKCE.")


def _resolve_consent(tenant: Tenant, user: User, client_app: ClientApp, requested_scopes: list[str], consent_accepted: bool) -> None:
    current = Consent.objects(tenant=tenant, user=user, client_app=client_app, revoked_at=None).first()
    if current and set(requested_scopes).issubset(set(current.scopes)):
        return
    if tenant.lgpd_consent_required and not consent_accepted:
        raise AuthenticationError("Consentimento LGPD obrigatorio para prosseguir.")


def _issue_email_mfa_code(user: User) -> None:
    code = generate_one_time_code()
    MfaChallenge.objects(user=user, consumed_at=None).delete()
    MfaChallenge(
        tenant=user.tenant,
        user=user,
        code_hash=hash_secret(code),
        method="EMAIL",
        expires_at=_utc_now_naive() + timedelta(seconds=get_settings().mfa_email_code_ttl_seconds),
    ).save()
    send_mfa_code_email_task.delay(str(user.tenant.id), str(user.id), code)


def _enforce_mfa(user: User, mfa_code: str | None) -> None:
    if not user.mfa_enabled:
        return
    if user.mfa_method == "EMAIL":
        if not mfa_code:
            _issue_email_mfa_code(user)
            capture_telemetry_task.delay(str(user.tenant.id), "mfa.challenge.sent", {"status": "SUCCESS", "user_id": str(user.id), "method": "EMAIL"})
            raise AuthenticationError(
                "Codigo MFA enviado por e-mail.",
                details={"mfa_required": True, "mfa_method": "EMAIL", "delivery": "email"},
            )
        challenge = MfaChallenge.objects(
            user=user,
            method="EMAIL",
            code_hash=hash_secret(mfa_code),
            consumed_at=None,
        ).first()
        now = _utc_now_naive()
        if challenge is None or challenge.expires_at <= now:
            raise AuthenticationError(
                "Codigo MFA invalido ou expirado.",
                details={"mfa_required": True, "mfa_method": "EMAIL"},
            )
        challenge.consumed_at = now
        challenge.save()
        return
    if not user.mfa_secret:
        raise AuthenticationError("MFA configurado de forma incompleta para este usuario.")
    if not mfa_code:
        raise AuthenticationError("Codigo MFA obrigatorio.", details={"mfa_required": True, "mfa_method": "TOTP"})
    if not verify_totp_code(user.mfa_secret, mfa_code):
        raise AuthenticationError("Codigo MFA invalido.", details={"mfa_required": True, "mfa_method": "TOTP"})


def _resolve_user_scopes(user: User, tenant: Tenant, client_app: ClientApp, requested_scopes: list[str]) -> list[str]:
    candidate_scopes = requested_scopes or client_app.allowed_scopes
    if any(scope not in client_app.allowed_scopes for scope in candidate_scopes):
        raise AuthenticationError("Escopo solicitado nao permitido para a aplicacao.")
    if user.role == "ADMIN":
        return candidate_scopes
    role_binding = RoleBinding.objects(
        tenant=tenant,
        user=user,
        client_app=client_app,
        status="ACTIVE",
    ).first()
    if role_binding is None:
        raise AuthenticationError("Usuario nao possui acesso ativo a esta aplicacao.")
    if role_binding.scopes:
        if any(scope not in role_binding.scopes for scope in candidate_scopes):
            raise AuthenticationError("Escopo solicitado nao permitido para este usuario nesta aplicacao.")
        return candidate_scopes
    return candidate_scopes


class OAuthService:
    @staticmethod
    def login(payload: dict) -> dict:
        data = LoginSchema.model_validate(payload)
        tenant, user = _authenticate_user(data.tenant_slug, data.email, data.password)
        _enforce_mfa(user, data.mfa_code)
        scopes = ["admin"]
        access_token, token_id, access_expires_at = issue_access_token(subject=str(user.id), tenant_id=str(tenant.id), scopes=scopes)
        refresh_token, refresh_token_hash = generate_opaque_token("rt")
        AuthSession(
            tenant=tenant,
            user=user,
            refresh_token_hash=refresh_token_hash,
            scopes=scopes,
            access_token_jti=token_id,
            expires_at=_utc_now_naive() + timedelta(days=get_settings().jwt_refresh_ttl_days),
        ).save()
        AuditLog(tenant=tenant, user=user, action="auth.login", actor_type="USER", status="SUCCESS").save()
        capture_telemetry_task.delay(str(tenant.id), "auth.login", {"status": "SUCCESS", "user_id": str(user.id)})
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_at": access_expires_at.isoformat(),
            "refresh_token": refresh_token,
            "scope": " ".join(scopes),
            "user": {
                "id": str(user.id),
                "tenant_id": str(tenant.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
            },
        }

    @staticmethod
    def authorize(payload: dict) -> dict:
        data = AuthorizeSchema.model_validate(payload)
        tenant, user = _authenticate_user(data.tenant_slug, data.email, data.password)
        _enforce_mfa(user, data.mfa_code)
        client_app = _validate_client(data.client_id, data.redirect_uri)
        if str(client_app.tenant.id) != str(tenant.id):
            raise AuthenticationError("Aplicacao nao pertence ao tenant informado.")
        requested_scopes = _resolve_user_scopes(user, tenant, client_app, data.scopes)
        _resolve_consent(tenant, user, client_app, requested_scopes, data.consent_accepted)
        code = f"ac_{secrets.token_urlsafe(24)}"
        auth_code = OAuthAuthorizationCode(
            tenant=tenant,
            user=user,
            client_app=client_app,
            code_hash=hash_secret(code),
            redirect_uri=data.redirect_uri,
            scopes=requested_scopes,
            code_challenge=data.code_challenge,
            code_challenge_method=data.code_challenge_method,
            expires_at=_utc_now_naive() + timedelta(seconds=get_settings().authorization_code_ttl_seconds),
        ).save()
        Consent.objects(tenant=tenant, user=user, client_app=client_app).modify(
            upsert=True,
            new=True,
            set__scopes=requested_scopes,
            set__granted_at=_utc_now_naive(),
            unset__revoked_at=1,
        )
        AuditLog(tenant=tenant, user=user, client_app=client_app, action="oauth.authorize", actor_type="USER", status="SUCCESS").save()
        capture_telemetry_task.delay(
            str(tenant.id),
            "oauth.authorize",
            {"status": "SUCCESS", "user_id": str(user.id), "client_app_id": str(client_app.id)},
        )
        return {
            "code": code,
            "state": data.state,
            "redirect_to": f"{data.redirect_uri}?code={code}" + (f"&state={data.state}" if data.state else ""),
            "expires_at": auth_code.expires_at.isoformat(),
        }

    @staticmethod
    def exchange_token(payload: dict) -> dict:
        data = TokenSchema.model_validate(payload)
        if data.grant_type == "authorization_code":
            if not data.client_id or not data.code or not data.redirect_uri:
                raise AuthenticationError("code e redirect_uri sao obrigatorios.")
            client_app = _validate_client(data.client_id, data.redirect_uri)
            _validate_client_secret(client_app, data.client_secret)
            auth_code = OAuthAuthorizationCode.objects(
                code_hash=hash_secret(data.code),
                client_app=client_app,
                consumed_at=None,
            ).first()
            if auth_code is None or _normalize_datetime(auth_code.expires_at) <= _utc_now_naive():
                raise AuthenticationError("Authorization code invalido ou expirado.")
            _validate_pkce(data.code_verifier, auth_code)
            access_token, token_id, access_expires_at = issue_access_token(
                subject=str(auth_code.user.id),
                tenant_id=str(auth_code.tenant.id),
                scopes=auth_code.scopes,
                audience=client_app.client_id,
            )
            refresh_token, refresh_token_hash = generate_opaque_token("rt")
            AuthSession(
                tenant=auth_code.tenant,
                user=auth_code.user,
                client_app=client_app,
                refresh_token_hash=refresh_token_hash,
                scopes=auth_code.scopes,
                access_token_jti=token_id,
                expires_at=_utc_now_naive() + timedelta(days=get_settings().jwt_refresh_ttl_days),
            ).save()
            auth_code.consumed_at = _utc_now_naive()
            auth_code.save()
            AuditLog(
                tenant=auth_code.tenant,
                user=auth_code.user,
                client_app=client_app,
                action="oauth.token",
                actor_type="USER",
                status="SUCCESS",
            ).save()
            capture_telemetry_task.delay(
                str(auth_code.tenant.id),
                "oauth.token",
                {"status": "SUCCESS", "user_id": str(auth_code.user.id), "client_app_id": str(client_app.id)},
            )
            return {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_at": access_expires_at.isoformat(),
                "refresh_token": refresh_token,
                "scope": " ".join(auth_code.scopes),
            }

        if not data.refresh_token:
            raise AuthenticationError("refresh_token obrigatorio.")
        session = AuthSession.objects(refresh_token_hash=hash_secret(data.refresh_token), revoked_at=None).first()
        if session is None or _normalize_datetime(session.expires_at) <= _utc_now_naive():
            raise AuthenticationError("Refresh token invalido ou expirado.")
        access_token, token_id, access_expires_at = issue_access_token(
            subject=str(session.user.id),
            tenant_id=str(session.tenant.id),
            scopes=session.scopes,
            audience=session.client_app.client_id if session.client_app else None,
        )
        new_refresh_token, new_refresh_token_hash = generate_opaque_token("rt")
        session.refresh_token_hash = new_refresh_token_hash
        session.access_token_jti = token_id
        session.expires_at = _utc_now_naive() + timedelta(days=get_settings().jwt_refresh_ttl_days)
        session.save()
        capture_telemetry_task.delay(
            str(session.tenant.id),
            "oauth.refresh",
            {"status": "SUCCESS", "user_id": str(session.user.id), "client_app_id": str(session.client_app.id) if session.client_app else None},
        )
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_at": access_expires_at.isoformat(),
            "refresh_token": new_refresh_token,
            "scope": " ".join(session.scopes),
        }

    @staticmethod
    def revoke(payload: dict) -> dict:
        data = RevokeSchema.model_validate(payload)
        if data.access_token:
            decoded = decode_access_token(data.access_token)
            expires_at = datetime.fromtimestamp(decoded["exp"], UTC)
            revoke_access_token(decoded["jti"], expires_at)
            tenant = Tenant.objects(id=decoded["tenant_id"]).first()
            user = User.objects(id=decoded["sub"]).first()
            if tenant and user:
                capture_telemetry_task.delay(str(tenant.id), "oauth.revoke", {"status": "SUCCESS", "user_id": str(user.id)})
                send_security_notification_task.delay(str(tenant.id), str(user.id), "Um token de acesso foi revogado.")
        if data.refresh_token:
            session = AuthSession.objects(refresh_token_hash=hash_secret(data.refresh_token), revoked_at=None).first()
            if session:
                session.revoked_at = _utc_now_naive()
                session.save()
                capture_telemetry_task.delay(
                    str(session.tenant.id),
                    "oauth.revoke_refresh",
                    {"status": "SUCCESS", "user_id": str(session.user.id), "client_app_id": str(session.client_app.id) if session.client_app else None},
                )
        return {"status": "revoked"}
