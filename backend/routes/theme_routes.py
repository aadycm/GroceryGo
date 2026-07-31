from flask import Blueprint, request
from database.db import db
from models import ThemeSettings
from models.role import ADMIN
from auth.decorators import token_required, roles_required
from utils.responses import success, error
from utils.validators import require_fields

bp = Blueprint("themes", __name__, url_prefix="/api/themes")


@bp.get("")
def list_themes():
    return success([t.to_dict() for t in ThemeSettings.query.all()])


@bp.get("/active")
def active_theme():
    theme = ThemeSettings.query.filter_by(is_active=True).first()
    if not theme:
        return success({"theme_name": "light", "colors": {}, "is_active": True})
    return success(theme.to_dict())


@bp.post("")
@token_required
@roles_required(ADMIN)
def create_theme():
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["theme_name"])
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 400)
    if payload["theme_name"] not in ("dark", "light", "custom"):
        return error("theme_name must be one of: dark, light, custom", 400)

    theme = ThemeSettings(theme_name=payload["theme_name"], colors=payload.get("colors", {}))
    db.session.add(theme)
    db.session.commit()
    return success(theme.to_dict(), "Theme created", 201)


@bp.put("/<int:theme_id>/activate")
@token_required
@roles_required(ADMIN)
def activate_theme(theme_id):
    theme = ThemeSettings.query.get(theme_id)
    if not theme:
        return error("Theme not found", 404)
    ThemeSettings.query.update({ThemeSettings.is_active: False})
    theme.is_active = True
    db.session.commit()
    return success(theme.to_dict(), "Theme activated")
