from flask import Blueprint, request, g
from sqlalchemy import or_
from database.db import db
from models import Notification
from models.role import ADMIN, MANAGER
from auth.decorators import token_required, roles_required
from services.notification_service import broadcast_notification
from utils.responses import success, error
from utils.validators import require_fields
from utils.pagination import paginate_query

bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@bp.get("")
@token_required
def list_notifications():
    user = g.current_user
    query = Notification.query.filter(
        or_(Notification.user_id == user.id, Notification.user_id.is_(None))
    ).order_by(Notification.created_at.desc())
    items, meta = paginate_query(query)
    return success([n.to_dict() for n in items], meta=meta)


@bp.put("/<int:notification_id>/read")
@token_required
def mark_read(notification_id):
    notification = Notification.query.get(notification_id)
    if not notification:
        return error("Notification not found", 404)
    notification.is_read = True
    db.session.commit()
    return success(notification.to_dict())


@bp.post("/broadcast")
@token_required
@roles_required(ADMIN, MANAGER)
def broadcast():
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["title", "message"])
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 400)
    n = broadcast_notification(payload["title"], payload["message"])
    return success(n.to_dict(), "Broadcast sent", 201)
