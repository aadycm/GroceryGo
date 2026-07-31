from database.db import db
from models import User, Customer, Role
from models.role import CUSTOMER
from auth.jwt_handler import generate_access_token, generate_refresh_token
from middleware.error_handlers import ApiError


def register_customer(name, email, password, phone=None, address=None, city=None, pincode=None):
    if User.query.filter_by(email=email.lower().strip()).first():
        raise ApiError("An account with this email already exists", 409)

    role = Role.query.filter_by(name=CUSTOMER).first()
    if not role:
        raise ApiError("Customer role is not configured", 500)

    user = User(name=name.strip(), email=email.lower().strip(), phone=phone, role_id=role.id)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()  # get user.id before creating the customer profile

    customer = Customer(user_id=user.id, address=address, city=city, pincode=pincode)
    db.session.add(customer)
    db.session.commit()

    return user


def authenticate(email, password):
    user = User.query.filter_by(email=email.lower().strip()).first()
    if not user or not user.check_password(password):
        raise ApiError("Invalid email or password", 401)
    if not user.is_active:
        raise ApiError("This account has been deactivated", 403)

    return {
        "access_token": generate_access_token(user),
        "refresh_token": generate_refresh_token(user),
        "user": user.to_dict(),
    }


def refresh_access_token(refresh_payload):
    user = User.query.get(int(refresh_payload["sub"]))
    if not user or not user.is_active:
        raise ApiError("User not found or inactive", 401)
    return generate_access_token(user)
