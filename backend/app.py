import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

from config.config import get_config
from database.db import db, migrate
from middleware.error_handlers import register_error_handlers
from middleware.cors_setup import init_cors
from middleware.rate_limiter import limiter


def create_app(config_object=None):
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "admin-dashboard", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "admin-dashboard", "static"),
    )
    app.config.from_object(config_object or get_config())

    db.init_app(app)
    migrate.init_app(app, db)
    init_cors(app)
    limiter.init_app(app)
    register_error_handlers(app)

    from routes import register_blueprints
    register_blueprints(app)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["QR_FOLDER"], exist_ok=True)
    os.makedirs(app.config["REPORT_FOLDER"], exist_ok=True)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
