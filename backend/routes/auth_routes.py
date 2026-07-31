import jwt
from flask import Blueprint, request, g
from database.db import db
from models import User
from auth.jwt_handler import decode_token
from auth.decorators import token_required
from services.auth_service import register_customer, authenticate, refresh_access_token
from utils.responses import success, error
from utils.validators import require_fields, is_valid_email
from middleware.error_handlers import ApiError

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["name", "email", "password"])
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 400)
    if not is_valid_email(payload["email"]):
        return error("Invalid email address", 400)
    if len(payload["password"]) < 8:
        return error("Password must be at least 8 characters", 400)

    user = register_customer(
        name=payload["name"],
        email=payload["email"],
        password=payload["password"],
        phone=payload.get("phone"),
        address=payload.get("address"),
        city=payload.get("city"),
        pincode=payload.get("pincode"),
    )
    return success(user.to_dict(), "Registration successful", 201)


@bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["email", "password"])
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 400)

    result = authenticate(payload["email"], payload["password"])
    return success(result, "Login successful")


@bp.post("/refresh")
def refresh():
    payload = request.get_json(silent=True) or {}
    token = payload.get("refresh_token")
    if not token:
        return error("refresh_token is required", 400)
    try:
        decoded = decode_token(token)
        if decoded.get("type") != "refresh":
            return error("Invalid token type", 401)
    except jwt.ExpiredSignatureError:
        return error("Refresh token has expired, please log in again", 401)
    except jwt.InvalidTokenError:
        return error("Invalid refresh token", 401)

    access_token = refresh_access_token(decoded)
    return success({"access_token": access_token})


@bp.get("/me")
@token_required
def me():
    return success(g.current_user.to_dict())
