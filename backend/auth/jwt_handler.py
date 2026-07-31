import jwt
from datetime import datetime, timezone
from flask import current_app


def _encode(payload, expires_delta):
    now = datetime.now(timezone.utc)
    payload = {
        **payload,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def generate_access_token(user):
    return _encode(
        {"sub": str(user.id), "role": user.role.name, "type": "access"},
        current_app.config["JWT_ACCESS_TOKEN_EXPIRES"],
    )


def generate_refresh_token(user):
    return _encode(
        {"sub": str(user.id), "type": "refresh"},
        current_app.config["JWT_REFRESH_TOKEN_EXPIRES"],
    )


def decode_token(token):
    """Returns the decoded payload dict, or raises jwt exceptions on failure."""
    return jwt.decode(
        token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
    )
