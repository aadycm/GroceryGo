from datetime import datetime, timezone
from database.db import db


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(
        db.Integer, db.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    plan_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default="active", nullable=False)  # active, expired, cancelled
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    customer = db.relationship("Customer", back_populates="subscriptions")

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "plan_name": self.plan_name,
            "status": self.status,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "amount": float(self.amount),
        }
