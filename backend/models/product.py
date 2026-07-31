from datetime import datetime, timezone
from database.db import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.String(1000))
    category_id = db.Column(
        db.Integer, db.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    price = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(30), default="pc", nullable=False)  # kg, pack, pc, litre
    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.CheckConstraint("price >= 0", name="ck_products_price_nonneg"),
    )

    category = db.relationship("Category", back_populates="products")
    inventory = db.relationship(
        "Inventory", back_populates="product", uselist=False, cascade="all, delete-orphan"
    )
    order_items = db.relationship("OrderItem", back_populates="product")

    def to_dict(self, include_stock=False):
        data = {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "description": self.description,
            "category_id": self.category_id,
            "category": self.category.name if self.category else None,
            "price": float(self.price),
            "unit": self.unit,
            "image_url": self.image_url,
            "is_active": self.is_active,
        }
        if include_stock and self.inventory:
            data["stock_quantity"] = self.inventory.quantity
            data["low_stock"] = self.inventory.quantity <= self.inventory.reorder_level
        return data
