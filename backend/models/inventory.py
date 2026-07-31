from datetime import datetime, timezone
from database.db import db


class Inventory(db.Model):
    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    quantity = db.Column(db.Integer, default=0, nullable=False)
    reorder_level = db.Column(db.Integer, default=10, nullable=False)
    reorder_quantity = db.Column(db.Integer, default=50, nullable=False)
    supplier_id = db.Column(
        db.Integer, db.ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True
    )
    last_restocked_at = db.Column(db.DateTime)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.CheckConstraint("quantity >= 0", name="ck_inventory_qty_nonneg"),
        db.Index("ix_inventory_low_stock", "quantity", "reorder_level"),
    )

    product = db.relationship("Product", back_populates="inventory")
    supplier = db.relationship("Supplier", back_populates="inventory_items")
    history = db.relationship(
        "InventoryHistory", back_populates="inventory", cascade="all, delete-orphan"
    )

    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_level

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "quantity": self.quantity,
            "reorder_level": self.reorder_level,
            "reorder_quantity": self.reorder_quantity,
            "supplier_id": self.supplier_id,
            "is_low_stock": self.is_low_stock,
            "last_restocked_at": self.last_restocked_at.isoformat()
            if self.last_restocked_at
            else None,
        }


class InventoryHistory(db.Model):
    __tablename__ = "inventory_history"

    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(
        db.Integer, db.ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False
    )
    change_qty = db.Column(db.Integer, nullable=False)  # +ve restock, -ve sale/adjust
    reason = db.Column(db.String(50), nullable=False)  # restock, sale, adjustment, return
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    inventory = db.relationship("Inventory", back_populates="history")

    def to_dict(self):
        return {
            "id": self.id,
            "inventory_id": self.inventory_id,
            "change_qty": self.change_qty,
            "reason": self.reason,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
