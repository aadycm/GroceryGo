from flask import Blueprint
from models import Product, Order
from auth.decorators import token_required
from services.qr_service import generate_product_qr, generate_order_qr
from utils.responses import success, error

bp = Blueprint("qr", __name__, url_prefix="/api/qr")


@bp.get("/product/<int:product_id>")
def product_qr(product_id):
    if not Product.query.get(product_id):
        return error("Product not found", 404)
    path = generate_product_qr(product_id)
    return success({"qr_code_path": path})


@bp.get("/order/<int:order_id>")
@token_required
def order_qr(order_id):
    if not Order.query.get(order_id):
        return error("Order not found", 404)
    path = generate_order_qr(order_id)
    return success({"qr_code_path": path})
