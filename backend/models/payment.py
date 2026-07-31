from datetime import datetime, timezone
from database.db import db

PAYMENT_METHODS = ["upi", "card", "netbanking", "cash"]
PAYMENT_STATUSES = ["pending", "success", "failed", "refunded"]


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    method = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False, index=True)
    razorpay_order_id = db.Column(db.String(100), index=True)
    razorpay_payment_id = db.Column(db.String(100), index=True)
    razorpay_signature = db.Column(db.String(255))
    transaction_ref = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.CheckConstraint("amount >= 0", name="ck_payments_amount_nonneg"),
    )

    order = db.relationship("Order", back_populates="payments")

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "method": self.method,
            "amount": float(self.amount),
            "status": self.status,
            "razorpay_order_id": self.razorpay_order_id,
            "razorpay_payment_id": self.razorpay_payment_id,
            "transaction_ref": self.transaction_ref,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
