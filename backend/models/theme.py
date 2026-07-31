from datetime import datetime, timezone
from database.db import db


class ThemeSettings(db.Model):
    __tablename__ = "theme_settings"

    id = db.Column(db.Integer, primary_key=True)
    theme_name = db.Column(db.String(20), nullable=False)  # dark, light, custom
    colors = db.Column(db.JSON, default=dict)
    is_active = db.Column(db.Boolean, default=False, nullable=False, index=True)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "theme_name": self.theme_name,
            "colors": self.colors,
            "is_active": self.is_active,
        }
