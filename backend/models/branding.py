from datetime import datetime, timezone
from database.db import db


class BrandingSettings(db.Model):
    __tablename__ = "branding_settings"

    id = db.Column(db.Integer, primary_key=True)
    app_name = db.Column(db.String(120), default="FreshMart", nullable=False)
    logo_url = db.Column(db.String(500))
    primary_color = db.Column(db.String(20), default="#2E7D32")
    secondary_color = db.Column(db.String(20), default="#FFC107")
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))

    def to_dict(self):
        return {
            "id": self.id,
            "app_name": self.app_name,
            "logo_url": self.logo_url,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
