from database.db import db

# Fixed role set used across auth + admin dashboard access control.
ADMIN = "admin"
MANAGER = "manager"
STAFF = "staff"
DELIVERY = "delivery"
CUSTOMER = "customer"
ALL_ROLES = [ADMIN, MANAGER, STAFF, DELIVERY, CUSTOMER]


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))

    users = db.relationship("User", back_populates="role")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description}
