import os
import uuid
from flask import Blueprint, request, g, current_app
from werkzeug.utils import secure_filename
from database.db import db
from models import BrandingSettings
from models.role import ADMIN
from auth.decorators import token_required, roles_required
from utils.responses import success, error

bp = Blueprint("branding", __name__, url_prefix="/api/branding")

ALLOWED_LOGO_EXT = {"png", "jpg", "jpeg", "svg", "webp"}


def _settings():
    settings = BrandingSettings.query.first()
    if not settings:
        settings = BrandingSettings()
        db.session.add(settings)
        db.session.commit()
    return settings


@bp.get("")
def get_branding():
    return success(_settings().to_dict())


@bp.put("")
@token_required
@roles_required(ADMIN)
def update_branding():
    settings = _settings()
    payload = request.get_json(silent=True) or {}
    for field in ("app_name", "primary_color", "secondary_color"):
        if field in payload:
            setattr(settings, field, payload[field])
    settings.updated_by = g.current_user.id
    db.session.commit()
    return success(settings.to_dict(), "Branding updated")


@bp.post("/logo")
@token_required
@roles_required(ADMIN)
def upload_logo():
    if "logo" not in request.files:
        return error("No 'logo' file part in request", 400)
    file = request.files["logo"]
    if file.filename == "":
        return error("No file selected", 400)
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_LOGO_EXT:
        return error(f"Unsupported file type. Allowed: {sorted(ALLOWED_LOGO_EXT)}", 400)

    filename = secure_filename(f"logo_{uuid.uuid4().hex}.{ext}")
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "branding")
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, filename))

    settings = _settings()
    settings.logo_url = f"/uploads/branding/{filename}"
    settings.updated_by = g.current_user.id
    db.session.commit()
    return success(settings.to_dict(), "Logo uploaded")
