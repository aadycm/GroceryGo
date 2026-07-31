from datetime import datetime, timezone
from database.db import db


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    address = db.Column(db.String(500))
    city = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    loyalty_points = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="customer_profile")
    orders = db.relationship(
        "Order", back_populates="customer", cascade="all, delete-orphan"
    )
    subscriptions = db.relationship(
        "Subscription", back_populates="customer", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.user.name if self.user else None,
            "email": self.user.email if self.user else None,
            "phone": self.user.phone if self.user else None,
            "address": self.address,
            "city": self.city,
            "pincode": self.pincode,
            "loyalty_points": self.loyalty_points,
        }
