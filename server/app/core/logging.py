import json
import logging
from datetime import UTC, datetime

from flask import Flask, g, request


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        request_id = getattr(record, "request_id", None) or getattr(g, "request_id", None)
        if request_id:
            payload["request_id"] = request_id
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(app: Flask) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    @app.after_request
    def add_request_id_header(response):  # type: ignore[no-untyped-def]
        request_id = getattr(g, "request_id", None)
        if request_id:
            response.headers["X-Request-Id"] = request_id
        return response


def request_log_context() -> dict[str, str]:
    return {
        "method": request.method,
        "path": request.path,
        "request_id": getattr(g, "request_id", ""),
    }
