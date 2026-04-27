from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Sylo SSO"
    app_env: str = Field(default="development", alias="FLASK_ENV")
    app_host: str = "0.0.0.0"
    app_port: int = 5000
    app_debug: bool = Field(default=False, alias="APP_DEBUG")

    api_version: str = "1.0.0"
    api_title: str = "Sylo SSO API"
    api_description: str = "Headless identity provider for multi-tenant B2B applications."

    mongodb_uri: str = Field(default="mongodb://localhost:27017/sylo_sso", alias="MONGODB_URI")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    frontend_url: str = Field(default="http://localhost:3000")
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    jwt_algorithm: str = "HS256"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 7
    jwt_issuer: str = "sylo-sso"
    jwt_audience: str = "sylo-clients"
    jwt_key_id: str = "current"

    telemetry_ttl_seconds: int = 60 * 60 * 24 * 30
    authorization_code_ttl_seconds: int = 300
    password_reset_ttl_seconds: int = 3600
    email_verification_ttl_seconds: int = 60 * 60 * 24
    rate_limit_window_seconds: int = 60
    rate_limit_max_requests: int = 30
    mfa_issuer: str = "Sylo SSO"
    mfa_step_seconds: int = 30
    mfa_digits: int = 6
    mfa_allowed_drift_windows: int = 1
    mfa_email_code_ttl_seconds: int = 600

    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = 0.0

    mailgun_base_url: str = "https://api.mailgun.net/v3"
    mailgun_domain: str | None = None
    mailgun_api_key: str | None = None
    mail_from_name: str = "Sylo SSO"
    mail_from_address: str = "noreply@sylo.local"

    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    model_config = SettingsConfigDict(
        env_file=("server/.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
