from dataclasses import dataclass, field
from http import HTTPStatus
import traceback

from flask import Flask, jsonify, g
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException


@dataclass(slots=True)
class AppError(Exception):
    message: str
    status_code: int = HTTPStatus.BAD_REQUEST
    code: str = "bad_request"
    details: dict | list | None = field(default=None)


class AuthenticationError(AppError):
    def __init__(self, message: str = "Autenticacao invalida.", details: dict | None = None) -> None:
        super().__init__(message=message, status_code=HTTPStatus.UNAUTHORIZED, code="unauthorized", details=details)


class AuthorizationError(AppError):
    def __init__(self, message: str = "Acesso negado.", details: dict | None = None) -> None:
        super().__init__(message=message, status_code=HTTPStatus.FORBIDDEN, code="forbidden", details=details)


class ConflictError(AppError):
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message=message, status_code=HTTPStatus.CONFLICT, code="conflict", details=details)


class NotFoundError(AppError):
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message=message, status_code=HTTPStatus.NOT_FOUND, code="not_found", details=details)


class RateLimitError(AppError):
    def __init__(self, message: str = "Limite de requisicoes excedido.", details: dict | None = None) -> None:
        super().__init__(message=message, status_code=HTTPStatus.TOO_MANY_REQUESTS, code="rate_limited", details=details)


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(error: AppError):  # type: ignore[no-untyped-def]
        return jsonify(_payload(error.code, error.message, error.details)), error.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):  # type: ignore[no-untyped-def]
        return jsonify(_payload("validation_error", "Dados invalidos.", error.errors())), HTTPStatus.UNPROCESSABLE_ENTITY

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):  # type: ignore[no-untyped-def]
        traceback.print_exc()
        return jsonify(_payload("http_error", error.description, None)), error.code or HTTPStatus.BAD_REQUEST

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):  # type: ignore[no-untyped-def]
        app.logger.exception("Unhandled application error", extra={"request_id": getattr(g, "request_id", None)})
        traceback.print_exc()
        return jsonify(_payload("internal_error", "Erro interno do servidor.", None)), HTTPStatus.INTERNAL_SERVER_ERROR


def _payload(code: str, message: str, details: dict | list | None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": getattr(g, "request_id", None),
        }
    }
