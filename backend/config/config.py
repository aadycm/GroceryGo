import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "30"))
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

    UPI_MERCHANT_VPA = os.getenv("UPI_MERCHANT_VPA", "")
    UPI_MERCHANT_NAME = os.getenv("UPI_MERCHANT_NAME", "FreshMart")

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "200 per hour")

    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.getenv("UPLOAD_FOLDER", "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "5")) * 1024 * 1024

    QR_FOLDER = os.path.join(BASE_DIR, "uploads", "qrcodes")
    REPORT_FOLDER = os.path.join(BASE_DIR, "uploads", "reports")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    # Falls back to local SQLite ONLY when DATABASE_URL is not supplied, so the
    # project can be booted immediately for local development/demoing without
    # requiring a running PostgreSQL instance. Production MUST set DATABASE_URL
    # to a postgresql:// URI.
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "dev.db")
    )


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config():
    """Returns the config class for the current FLASK_ENV. Validated here
    (not at class-definition/import time) so importing this module never
    fails on its own — only actually selecting production without a
    DATABASE_URL does, and with a clear error message.
    """
    env = os.getenv("FLASK_ENV", "development")
    config_cls = config_by_name.get(env, DevelopmentConfig)
    if config_cls is ProductionConfig and not os.getenv("DATABASE_URL"):
        raise RuntimeError(
            "DATABASE_URL environment variable is required in production "
            "and must point to a PostgreSQL instance, e.g. "
            "postgresql://user:pass@host:5432/grocerygo"
        )
    return config_cls
