from flask import Blueprint, request, g
from database.db import db
from models import Category
from models.role import ADMIN, MANAGER
from auth.decorators import token_required, roles_required
from utils.responses import success, error
from utils.validators import require_fields
from middleware.error_handlers import ApiError

bp = Blueprint("categories", __name__, url_prefix="/api/categories")


@bp.get("")
def list_categories():
    categories = Category.query.order_by(Category.name).all()
    return success([c.to_dict() for c in categories])


@bp.get("/<int:category_id>")
def get_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return error("Category not found", 404)
    return success(category.to_dict())


@bp.post("")
@token_required
@roles_required(ADMIN, MANAGER)
def create_category():
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["name"])
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 400)
    if Category.query.filter_by(name=payload["name"]).first():
        return error("A category with this name already exists", 409)

    category = Category(
        name=payload["name"],
        description=payload.get("description"),
        image_url=payload.get("image_url"),
    )
    db.session.add(category)
    db.session.commit()
    return success(category.to_dict(), "Category created", 201)


@bp.put("/<int:category_id>")
@token_required
@roles_required(ADMIN, MANAGER)
def update_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return error("Category not found", 404)
    payload = request.get_json(silent=True) or {}
    for field in ("name", "description", "image_url"):
        if field in payload:
            setattr(category, field, payload[field])
    db.session.commit()
    return success(category.to_dict(), "Category updated")


@bp.delete("/<int:category_id>")
@token_required
@roles_required(ADMIN)
def delete_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return error("Category not found", 404)
    db.session.delete(category)
    db.session.commit()
    return success(None, "Category deleted")
