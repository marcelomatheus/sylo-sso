from __future__ import annotations

from collections.abc import Callable
from functools import wraps

from flask import g, request

from app.core.errors import AuthenticationError, AuthorizationError
from app.core.security import decode_access_token, hash_secret
from app.models import ApiKey, User


def bearer_auth(required_scopes: list[str] | None = None, admin_only: bool = False) -> Callable:
    required_scopes = required_scopes or []

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                raise AuthenticationError("Bearer token obrigatorio.")
            token = header.removeprefix("Bearer ").strip()
            payload = decode_access_token(token)
            user = User.objects(id=payload["sub"]).first()
            if user is None:
                raise AuthenticationError("Usuario da sessao nao encontrado.")
            if str(user.tenant.id) != str(payload["tenant_id"]):
                raise AuthenticationError("Tenant do token nao corresponde ao usuario.")
            if admin_only and user.role != "ADMIN":
                raise AuthorizationError("Apenas administradores podem acessar este recurso.")
            token_scopes = set(payload.get("scope", "").split())
            if any(scope not in token_scopes for scope in required_scopes):
                raise AuthorizationError("Escopo insuficiente.")
            g.current_user = user
            g.current_token = payload
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def api_key_auth(required_scopes: list[str] | None = None) -> Callable:
    required_scopes = required_scopes or []

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                raise AuthenticationError("API Key obrigatoria.")
            token = header.removeprefix("Bearer ").strip()
            key_hash = hash_secret(token)
            api_key = ApiKey.objects(key_hash=key_hash, status="ACTIVE").first()
            if api_key is None:
                raise AuthenticationError("API Key invalida.")
            scopes = set(api_key.scopes)
            if any(scope not in scopes for scope in required_scopes):
                raise AuthorizationError("Escopo da API Key insuficiente.")
            g.current_api_key = api_key
            return fn(*args, **kwargs)

        return wrapper

    return decorator
