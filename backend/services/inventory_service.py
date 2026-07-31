from datetime import datetime, timezone
from database.db import db
from models import Inventory, InventoryHistory, Product
from middleware.error_handlers import ApiError


def adjust_stock(product_id, change_qty, reason, user_id=None):
    """Applies a signed quantity change to a product's inventory and logs history.
    reason: one of 'restock', 'sale', 'adjustment', 'return'
    """
    inventory = Inventory.query.filter_by(product_id=product_id).first()
    if not inventory:
        raise ApiError("Inventory record not found for this product", 404)

    new_qty = inventory.quantity + change_qty
    if new_qty < 0:
        raise ApiError("Insufficient stock for this operation", 409)

    inventory.quantity = new_qty
    if reason == "restock":
        inventory.last_restocked_at = datetime.now(timezone.utc)

    history = InventoryHistory(
        inventory_id=inventory.id, change_qty=change_qty, reason=reason, created_by=user_id
    )
    db.session.add(history)
    db.session.commit()
    return inventory


def reserve_stock_for_order(order_items, user_id=None):
    """order_items: list of {product_id, quantity}. Raises if any item is out of stock."""
    for item in order_items:
        inventory = Inventory.query.filter_by(product_id=item["product_id"]).first()
        if not inventory or inventory.quantity < item["quantity"]:
            product = Product.query.get(item["product_id"])
            name = product.name if product else item["product_id"]
            raise ApiError(f"Insufficient stock for '{name}'", 409)

    for item in order_items:
        adjust_stock(item["product_id"], -item["quantity"], "sale", user_id)


def restore_stock_for_cancelled_order(order_items, user_id=None):
    for item in order_items:
        adjust_stock(item["product_id"], item["quantity"], "return", user_id)


def get_low_stock_items():
    return [inv for inv in Inventory.query.all() if inv.is_low_stock]


def get_reorder_suggestions():
    low_stock = get_low_stock_items()
    return [
        {
            "product_id": inv.product_id,
            "product_name": inv.product.name if inv.product else None,
            "current_quantity": inv.quantity,
            "reorder_level": inv.reorder_level,
            "suggested_reorder_quantity": inv.reorder_quantity,
            "supplier_id": inv.supplier_id,
            "supplier_name": inv.supplier.name if inv.supplier else None,
        }
        for inv in low_stock
    ]
