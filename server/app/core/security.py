from __future__ import annotations

import hashlib
import hmac
import secrets
import struct
from datetime import UTC, datetime, timedelta
from urllib.parse import quote

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings
from app.core.errors import AuthenticationError
from app.core.redis_store import redis_store


password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    token = f"sk_{secrets.token_urlsafe(32)}"
    prefix = token[:12]
    return token, prefix, hash_secret(token)


def generate_client_credentials() -> tuple[str, str]:
    client_id = f"client_{secrets.token_urlsafe(12)}"
    client_secret = secrets.token_urlsafe(32)
    return client_id, client_secret


def issue_access_token(*, subject: str, tenant_id: str, scopes: list[str], audience: str | None = None) -> tuple[str, str, datetime]:
    settings = get_settings()
    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=settings.jwt_access_ttl_minutes)
    token_id = secrets.token_urlsafe(18)
    payload = {
        "iss": settings.jwt_issuer,
        "sub": subject,
        "aud": audience or settings.jwt_audience,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": token_id,
        "tenant_id": tenant_id,
        "scope": " ".join(scopes),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm, headers={"kid": settings.jwt_key_id})
    return token, token_id, expires_at


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Token invalido.") from exc
    if redis_store.is_denied(payload["jti"]):
        raise AuthenticationError("Token revogado.")
    return payload


def revoke_access_token(token_id: str, expires_at: datetime) -> None:
    ttl_seconds = max(int((expires_at - datetime.now(UTC)).total_seconds()), 1)
    redis_store.deny_token(token_id, ttl_seconds)


def generate_opaque_token(prefix: str) -> tuple[str, str]:
    token = f"{prefix}_{secrets.token_urlsafe(36)}"
    return token, hash_secret(token)


def generate_one_time_code(length: int = 6) -> str:
    upper_bound = 10**length
    return str(secrets.randbelow(upper_bound)).zfill(length)


def generate_totp_secret() -> str:
    return secrets.token_bytes(20).hex().upper()


def build_totp_uri(secret: str, account_name: str, tenant_slug: str | None = None) -> str:
    issuer = get_settings().mfa_issuer if tenant_slug is None else f"{get_settings().mfa_issuer} ({tenant_slug})"
    label = quote(f"{issuer}:{account_name}")
    return f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer)}&digits={get_settings().mfa_digits}&period={get_settings().mfa_step_seconds}"


def _totp_code(secret: str, timestamp: int) -> str:
    settings = get_settings()
    counter = int(timestamp / settings.mfa_step_seconds)
    secret_bytes = bytes.fromhex(secret)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(secret_bytes, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    code = binary % (10**settings.mfa_digits)
    return str(code).zfill(settings.mfa_digits)


def verify_totp_code(secret: str, code: str) -> bool:
    normalized = code.strip().replace(" ", "")
    if not normalized.isdigit():
        return False
    settings = get_settings()
    now = int(datetime.now(UTC).timestamp())
    for offset in range(-settings.mfa_allowed_drift_windows, settings.mfa_allowed_drift_windows + 1):
        candidate = _totp_code(secret, now + (offset * settings.mfa_step_seconds))
        if hmac.compare_digest(candidate, normalized):
            return True
    return False
