from datetime import datetime, timezone
from database.db import db

ORDER_STATUSES = [
    "pending", "confirmed", "preparing", "out_for_delivery", "delivered", "cancelled",
]


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(
        db.Integer, db.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    status = db.Column(db.String(30), default="pending", nullable=False, index=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    delivery_address = db.Column(db.String(500), nullable=False)
    assigned_delivery_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    placed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.CheckConstraint("total_amount >= 0", name="ck_orders_total_nonneg"),
    )

    customer = db.relationship("Customer", back_populates="orders")
    items = db.relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    payments = db.relationship(
        "Payment", back_populates="order", cascade="all, delete-orphan"
    )
    delivery_agent = db.relationship("User", foreign_keys=[assigned_delivery_id])

    def to_dict(self, include_items=True):
        data = {
            "id": self.id,
            "customer_id": self.customer_id,
            "status": self.status,
            "total_amount": float(self.total_amount),
            "delivery_address": self.delivery_address,
            "assigned_delivery_id": self.assigned_delivery_id,
            "placed_at": self.placed_at.isoformat() if self.placed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_items:
            data["items"] = [i.to_dict() for i in self.items]
        return data


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        db.CheckConstraint("quantity > 0", name="ck_order_items_qty_positive"),
    )

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product", back_populates="order_items")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "subtotal": float(self.subtotal),
        }
