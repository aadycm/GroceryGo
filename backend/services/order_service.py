from decimal import Decimal
from database.db import db
from models import Order, OrderItem, Product, Customer
from models.order import ORDER_STATUSES
from services.inventory_service import reserve_stock_for_order, restore_stock_for_cancelled_order
from services.notification_service import notify_user
from middleware.error_handlers import ApiError

VALID_TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"preparing", "cancelled"},
    "preparing": {"out_for_delivery", "cancelled"},
    "out_for_delivery": {"delivered", "cancelled"},
    "delivered": set(),
    "cancelled": set(),
}


def create_order(customer_id, items, delivery_address, user_id=None):
    """items: list of {product_id, quantity}"""
    if not items:
        raise ApiError("Order must contain at least one item", 400)

    customer = Customer.query.get(customer_id)
    if not customer:
        raise ApiError("Customer not found", 404)

    products = {p.id: p for p in Product.query.filter(
        Product.id.in_([i["product_id"] for i in items])
    ).all()}
    for item in items:
        if item["product_id"] not in products:
            raise ApiError(f"Product {item['product_id']} does not exist", 404)
        if item.get("quantity", 0) <= 0:
            raise ApiError("Item quantity must be greater than zero", 400)

    reserve_stock_for_order(items, user_id=user_id)

    order = Order(customer_id=customer_id, delivery_address=delivery_address, status="pending")
    db.session.add(order)
    db.session.flush()

    total = Decimal("0")
    for item in items:
        product = products[item["product_id"]]
        subtotal = Decimal(str(product.price)) * item["quantity"]
        total += subtotal
        db.session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item["quantity"],
                unit_price=product.price,
                subtotal=subtotal,
            )
        )

    order.total_amount = total
    db.session.commit()

    notify_user(
        customer.user_id,
        "Order placed",
        f"Your order #{order.id} has been placed successfully.",
    )
    return order


def update_order_status(order_id, new_status, user_id=None):
    order = Order.query.get(order_id)
    if not order:
        raise ApiError("Order not found", 404)
    if new_status not in ORDER_STATUSES:
        raise ApiError(f"Invalid status. Must be one of {ORDER_STATUSES}", 400)
    if new_status not in VALID_TRANSITIONS.get(order.status, set()):
        raise ApiError(
            f"Cannot transition order from '{order.status}' to '{new_status}'", 409
        )

    if new_status == "cancelled":
        items = [{"product_id": i.product_id, "quantity": i.quantity} for i in order.items]
        restore_stock_for_cancelled_order(items, user_id=user_id)

    order.status = new_status
    db.session.commit()

    notify_user(
        order.customer.user_id,
        "Order status updated",
        f"Your order #{order.id} is now '{new_status}'.",
    )
    return order


def assign_delivery(order_id, delivery_user_id):
    order = Order.query.get(order_id)
    if not order:
        raise ApiError("Order not found", 404)
    order.assigned_delivery_id = delivery_user_id
    db.session.commit()
    return order


def cancel_order(order_id, user_id=None):
    return update_order_status(order_id, "cancelled", user_id=user_id)
