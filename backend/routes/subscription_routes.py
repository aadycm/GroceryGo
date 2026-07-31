from flask import Blueprint, request, g
from database.db import db
from models import Subscription, Customer
from models.role import ADMIN, MANAGER, CUSTOMER
from auth.decorators import token_required, roles_required
from utils.responses import success, error
from utils.validators import require_fields
from utils.pagination import paginate_query

bp = Blueprint("subscriptions", __name__, url_prefix="/api/subscriptions")


@bp.get("")
@token_required
def list_subscriptions():
    user = g.current_user
    query = Subscription.query
    if user.role.name == CUSTOMER:
        customer = Customer.query.filter_by(user_id=user.id).first()
        if not customer:
            return error("No customer profile found", 403)
        query = query.filter_by(customer_id=customer.id)
    items, meta = paginate_query(query)
    return success([s.to_dict() for s in items], meta=meta)


@bp.post("")
@token_required
@roles_required(ADMIN, MANAGER)
def create_subscription():
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["customer_id", "plan_name", "start_date", "end_date", "amount"])
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 400)
    sub = Subscription(
        customer_id=payload["customer_id"],
        plan_name=payload["plan_name"],
        start_date=payload["start_date"],
        end_date=payload["end_date"],
        amount=payload["amount"],
        status=payload.get("status", "active"),
    )
    db.session.add(sub)
    db.session.commit()
    return success(sub.to_dict(), "Subscription created", 201)


@bp.put("/<int:sub_id>")
@token_required
@roles_required(ADMIN, MANAGER)
def update_subscription(sub_id):
    sub = Subscription.query.get(sub_id)
    if not sub:
        return error("Subscription not found", 404)
    payload = request.get_json(silent=True) or {}
    for field in ("plan_name", "status", "start_date", "end_date", "amount"):
        if field in payload:
            setattr(sub, field, payload[field])
    db.session.commit()
    return success(sub.to_dict(), "Subscription updated")
