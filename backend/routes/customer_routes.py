from flask import Blueprint, request, g
from database.db import db
from models import Customer
from models.role import ADMIN, MANAGER, CUSTOMER
from auth.decorators import token_required, roles_required
from utils.responses import success, error
from utils.pagination import paginate_query, apply_sorting

bp = Blueprint("customers", __name__, url_prefix="/api/customers")


@bp.get("")
@token_required
@roles_required(ADMIN, MANAGER)
def list_customers():
    query = apply_sorting(Customer.query, Customer, default_field="id")
    items, meta = paginate_query(query)
    return success([c.to_dict() for c in items], meta=meta)


@bp.get("/<int:customer_id>")
@token_required
def get_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        return error("Customer not found", 404)
    user = g.current_user
    if user.role.name == CUSTOMER and customer.user_id != user.id:
        return error("Forbidden", 403)
    return success(customer.to_dict())


@bp.put("/<int:customer_id>")
@token_required
def update_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        return error("Customer not found", 404)
    user = g.current_user
    if user.role.name == CUSTOMER and customer.user_id != user.id:
        return error("Forbidden", 403)

    payload = request.get_json(silent=True) or {}
    for field in ("address", "city", "pincode"):
        if field in payload:
            setattr(customer, field, payload[field])
    if "name" in payload and customer.user:
        customer.user.name = payload["name"]
    if "phone" in payload and customer.user:
        customer.user.phone = payload["phone"]
    db.session.commit()
    return success(customer.to_dict(), "Profile updated")
