from __future__ import annotations

from asyncio.log import logger
import traceback
from uuid import uuid4

from flask import Response, g
from flask_cors import CORS
from flask_openapi3 import Info, OpenAPI
from mongoengine import connect
from mongoengine.connection import ConnectionFailure, get_connection
import traceback
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.sentry import init_sentry
from app.commands import seed_db
from app.modules.access.routes.internal import access_internal_api
from app.modules.applications.routes.internal import applications_internal_api
from app.modules.auth.routes.external import auth_external_api
from app.modules.observability.routes.internal import observability_internal_api
from app.modules.tenants.routes.external import tenants_external_api
from app.modules.tenants.routes.internal import tenants_internal_api
from app.modules.users.routes.internal import users_internal_api


def create_app() -> OpenAPI:
    settings = get_settings()
    info = Info(title=settings.api_title, version=settings.api_version, description=settings.api_description)
    app = OpenAPI(
        __name__,
        info=info,
        doc_prefix="/docs",
        doc_url="/openapi.json",
        validation_error_status=422,
    )
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["JSON_SORT_KEYS"] = False
    CORS(
        app,
        resources={
            r"/*": {
                "origins": ["http://localhost:3000"], 
                
                "supports_credentials": True,
                
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                
                "expose_headers": ["Content-Type", "Authorization"]
            }
        }
    )
    configure_logging(app)
    init_sentry()
    
    
    
    try:
        get_connection(alias="default")
    except ConnectionFailure:
        connect(host=settings.mongodb_uri, alias="default", uuidRepresentation="standard")

    @app.before_request
    def assign_request_id() -> None:
        g.request_id = uuid4().hex

    @app.get("/health", doc_ui=False)
    def health() -> tuple[dict, int]:
        return {
            "status": "ok",
            "service": settings.app_name,
            "environment": settings.app_env,
        }, 200

    @app.get("/health/dependencies", doc_ui=False)
    def dependency_health() -> tuple[dict, int]:
        return {"status": "ok", "dependencies": {"mongo": "configured", "redis": "configured"}}, 200

    @app.get("/docs/scalar", doc_ui=False)
    def scalar_docs() -> Response:
        html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{settings.api_title} - Scalar</title>
  </head>
  <body>
    <script id="api-reference" data-url="/docs/openapi.json"></script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
  </body>
</html>"""
        return Response(html, mimetype="text/html")

    app.register_api(tenants_internal_api, url_prefix="/api/v1/tenants/internal")
    app.register_api(tenants_external_api, url_prefix="/api/v1/tenants/external")
    app.register_api(users_internal_api, url_prefix="/api/v1/users/internal")
    app.register_api(applications_internal_api, url_prefix="/api/v1/applications/internal")
    app.register_api(access_internal_api, url_prefix="/api/v1/access/internal")
    app.register_api(auth_external_api, url_prefix="/api/v1/auth/external")
    app.register_api(observability_internal_api, url_prefix="/api/v1/observability/internal")

    register_error_handlers(app)
    app.cli.add_command(seed_db)
    return app
