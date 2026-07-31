from flask import Blueprint, request
from database.db import db
from models import Supplier
from models.role import ADMIN, MANAGER
from auth.decorators import token_required, roles_required
from utils.responses import success, error
from utils.validators import require_fields
from utils.pagination import paginate_query

bp = Blueprint("suppliers", __name__, url_prefix="/api/suppliers")


@bp.get("")
@token_required
@roles_required(ADMIN, MANAGER)
def list_suppliers():
    items, meta = paginate_query(Supplier.query)
    return success([s.to_dict() for s in items], meta=meta)


@bp.post("")
@token_required
@roles_required(ADMIN, MANAGER)
def create_supplier():
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["name"])
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 400)
    supplier = Supplier(
        name=payload["name"],
        contact_person=payload.get("contact_person"),
        phone=payload.get("phone"),
        email=payload.get("email"),
        address=payload.get("address"),
    )
    db.session.add(supplier)
    db.session.commit()
    return success(supplier.to_dict(), "Supplier created", 201)


@bp.put("/<int:supplier_id>")
@token_required
@roles_required(ADMIN, MANAGER)
def update_supplier(supplier_id):
    supplier = Supplier.query.get(supplier_id)
    if not supplier:
        return error("Supplier not found", 404)
    payload = request.get_json(silent=True) or {}
    for field in ("name", "contact_person", "phone", "email", "address"):
        if field in payload:
            setattr(supplier, field, payload[field])
    db.session.commit()
    return success(supplier.to_dict(), "Supplier updated")


@bp.delete("/<int:supplier_id>")
@token_required
@roles_required(ADMIN)
def delete_supplier(supplier_id):
    supplier = Supplier.query.get(supplier_id)
    if not supplier:
        return error("Supplier not found", 404)
    db.session.delete(supplier)
    db.session.commit()
    return success(None, "Supplier deleted")
