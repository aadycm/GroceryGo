from flask import Blueprint, request, g
from database.db import db
from models import Inventory, InventoryHistory
from models.role import ADMIN, MANAGER, STAFF
from auth.decorators import token_required, roles_required
from services.inventory_service import adjust_stock, get_low_stock_items, get_reorder_suggestions
from utils.responses import success, error
from utils.validators import require_fields
from utils.pagination import paginate_query

bp = Blueprint("inventory", __name__, url_prefix="/api/inventory")


@bp.get("")
@token_required
@roles_required(ADMIN, MANAGER, STAFF)
def list_inventory():
    query = Inventory.query
    items, meta = paginate_query(query)
    return success([i.to_dict() for i in items], meta=meta)


@bp.get("/low-stock")
@token_required
@roles_required(ADMIN, MANAGER, STAFF)
def low_stock():
    return success([i.to_dict() for i in get_low_stock_items()])


@bp.get("/reorder-suggestions")
@token_required
@roles_required(ADMIN, MANAGER)
def reorder_suggestions():
    return success(get_reorder_suggestions())


@bp.put("/<int:product_id>")
@token_required
@roles_required(ADMIN, MANAGER)
def update_inventory_settings(product_id):
    inventory = Inventory.query.filter_by(product_id=product_id).first()
    if not inventory:
        return error("Inventory record not found", 404)
    payload = request.get_json(silent=True) or {}
    for field in ("reorder_level", "reorder_quantity", "supplier_id"):
        if field in payload:
            setattr(inventory, field, payload[field])
    db.session.commit()
    return success(inventory.to_dict(), "Inventory settings updated")


@bp.post("/<int:product_id>/adjust")
@token_required
@roles_required(ADMIN, MANAGER, STAFF)
def adjust(product_id):
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["change_qty", "reason"])
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 400)
    if payload["reason"] not in ("restock", "sale", "adjustment", "return"):
        return error("reason must be one of: restock, sale, adjustment, return", 400)

    inventory = adjust_stock(
        product_id, int(payload["change_qty"]), payload["reason"], user_id=g.current_user.id
    )
    return success(inventory.to_dict(), "Stock updated")


@bp.get("/<int:product_id>/history")
@token_required
@roles_required(ADMIN, MANAGER, STAFF)
def history(product_id):
    inventory = Inventory.query.filter_by(product_id=product_id).first()
    if not inventory:
        return error("Inventory record not found", 404)
    records = (
        InventoryHistory.query.filter_by(inventory_id=inventory.id)
        .order_by(InventoryHistory.created_at.desc())
        .all()
    )
    return success([r.to_dict() for r in records])
