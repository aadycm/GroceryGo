from flask import Blueprint, request, g
from models import Order, Customer
from models.role import ADMIN, MANAGER, STAFF, DELIVERY, CUSTOMER
from auth.decorators import token_required, roles_required
from services.order_service import create_order, update_order_status, assign_delivery, cancel_order
from services.qr_service import generate_order_qr
from utils.responses import success, error
from utils.validators import require_fields
from utils.pagination import paginate_query, apply_sorting
from middleware.error_handlers import ApiError

bp = Blueprint("orders", __name__, url_prefix="/api/orders")


def _customer_or_403(user):
    customer = Customer.query.filter_by(user_id=user.id).first()
    if not customer:
        raise ApiError("No customer profile associated with this account", 403)
    return customer


@bp.get("")
@token_required
def list_orders():
    user = g.current_user
    query = Order.query

    if user.role.name == CUSTOMER:
        customer = _customer_or_403(user)
        query = query.filter_by(customer_id=customer.id)
    elif user.role.name == DELIVERY:
        query = query.filter_by(assigned_delivery_id=user.id)
    # admin/manager/staff see all orders

    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)

    query = apply_sorting(query, Order, default_field="placed_at", default_dir="desc")
    items, meta = paginate_query(query)
    return success([o.to_dict() for o in items], meta=meta)


@bp.get("/<int:order_id>")
@token_required
def get_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return error("Order not found", 404)
    user = g.current_user
    if user.role.name == CUSTOMER:
        customer = _customer_or_403(user)
        if order.customer_id != customer.id:
            return error("Forbidden", 403)
    return success(order.to_dict())


@bp.post("")
@token_required
def place_order():
    user = g.current_user
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["items", "delivery_address"])
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 400)

    if user.role.name == CUSTOMER:
        customer = _customer_or_403(user)
        customer_id = customer.id
    else:
        customer_id = payload.get("customer_id")
        if not customer_id:
            return error("customer_id is required when placing on behalf of a customer", 400)

    order = create_order(customer_id, payload["items"], payload["delivery_address"], user_id=user.id)
    return success(order.to_dict(), "Order placed", 201)


@bp.put("/<int:order_id>/status")
@token_required
@roles_required(ADMIN, MANAGER, STAFF)
def change_status(order_id):
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["status"])
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 400)
    order = update_order_status(order_id, payload["status"], user_id=g.current_user.id)
    return success(order.to_dict(), "Order status updated")


@bp.put("/<int:order_id>/assign-delivery")
@token_required
@roles_required(ADMIN, MANAGER)
def assign(order_id):
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["delivery_user_id"])
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 400)
    order = assign_delivery(order_id, payload["delivery_user_id"])
    return success(order.to_dict(), "Delivery agent assigned")


@bp.post("/<int:order_id>/cancel")
@token_required
def cancel(order_id):
    order = Order.query.get(order_id)
    if not order:
        return error("Order not found", 404)
    user = g.current_user
    if user.role.name == CUSTOMER:
        customer = _customer_or_403(user)
        if order.customer_id != customer.id:
            return error("Forbidden", 403)
    order = cancel_order(order_id, user_id=user.id)
    return success(order.to_dict(), "Order cancelled")


@bp.get("/<int:order_id>/track")
@token_required
def track(order_id):
    order = Order.query.get(order_id)
    if not order:
        return error("Order not found", 404)
    return success(
        {
            "order_id": order.id,
            "status": order.status,
            "assigned_delivery_id": order.assigned_delivery_id,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
        }
    )


@bp.get("/<int:order_id>/qr")
@token_required
def order_qr(order_id):
    order = Order.query.get(order_id)
    if not order:
        return error("Order not found", 404)
    path = generate_order_qr(order.id)
    return success({"qr_code_path": path})
