from flask import Blueprint, request, g
from sqlalchemy import or_
from database.db import db
from models import Product, Inventory
from models.role import ADMIN, MANAGER
from auth.decorators import token_required, roles_required
from utils.responses import success, error
from utils.validators import require_fields
from utils.pagination import paginate_query, apply_sorting

bp = Blueprint("products", __name__, url_prefix="/api/products")


@bp.get("")
def list_products():
    query = Product.query.filter_by(is_active=True)

    search = request.args.get("search")
    if search:
        query = query.filter(
            or_(Product.name.ilike(f"%{search}%"), Product.description.ilike(f"%{search}%"))
        )

    category_id = request.args.get("category_id", type=int)
    if category_id:
        query = query.filter_by(category_id=category_id)

    min_price = request.args.get("min_price", type=float)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    max_price = request.args.get("max_price", type=float)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    query = apply_sorting(query, Product, default_field="name")
    items, meta = paginate_query(query)
    return success([p.to_dict(include_stock=True) for p in items], meta=meta)


@bp.get("/<int:product_id>")
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return error("Product not found", 404)
    return success(product.to_dict(include_stock=True))


@bp.post("")
@token_required
@roles_required(ADMIN, MANAGER)
def create_product():
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["sku", "name", "price"])
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 400)
    if Product.query.filter_by(sku=payload["sku"]).first():
        return error("A product with this SKU already exists", 409)

    product = Product(
        sku=payload["sku"],
        name=payload["name"],
        description=payload.get("description"),
        category_id=payload.get("category_id"),
        price=payload["price"],
        unit=payload.get("unit", "pc"),
        image_url=payload.get("image_url"),
    )
    db.session.add(product)
    db.session.flush()

    inventory = Inventory(
        product_id=product.id,
        quantity=payload.get("initial_quantity", 0),
        reorder_level=payload.get("reorder_level", 10),
        reorder_quantity=payload.get("reorder_quantity", 50),
        supplier_id=payload.get("supplier_id"),
    )
    db.session.add(inventory)
    db.session.commit()
    return success(product.to_dict(include_stock=True), "Product created", 201)


@bp.put("/<int:product_id>")
@token_required
@roles_required(ADMIN, MANAGER)
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return error("Product not found", 404)
    payload = request.get_json(silent=True) or {}
    for field in ("name", "description", "category_id", "price", "unit", "image_url", "is_active"):
        if field in payload:
            setattr(product, field, payload[field])
    db.session.commit()
    return success(product.to_dict(include_stock=True), "Product updated")


@bp.delete("/<int:product_id>")
@token_required
@roles_required(ADMIN)
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return error("Product not found", 404)
    product.is_active = False  # soft delete keeps historical order references valid
    db.session.commit()
    return success(None, "Product deactivated")
