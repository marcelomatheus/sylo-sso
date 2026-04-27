from app import create_app
from app.core.config import get_settings


settings = get_settings()
app = create_app()


if __name__ == "__main__":
    app.run(host=settings.app_host, port=settings.app_port, debug=settings.app_debug)
