import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, BACKEND_DIR)

import pytest

TEST_DB_PATH = "/tmp/test_grocerygo.db"
os.environ["FLASK_ENV"] = "testing"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

from app import create_app
from database.db import db as _db
from config.config import TestingConfig
from models import Role
from models.role import ALL_ROLES
from services.auth_service import register_customer


class _TestConfig(TestingConfig):
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{TEST_DB_PATH}"


@pytest.fixture(scope="session")
def app():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    application = create_app(_TestConfig)
    with application.app_context():
        _db.create_all()
        for name in ALL_ROLES:
            _db.session.add(Role(name=name, description=name.capitalize()))
        _db.session.commit()
        yield application
        _db.session.remove()
        _db.drop_all()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_session(app):
    with app.app_context():
        yield _db.session


def _login(client, email, password):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.get_json()
    return res.get_json()["data"]["access_token"]


@pytest.fixture()
def admin_token(app, client):
    with app.app_context():
        role = Role.query.filter_by(name="admin").first()
        from models import User

        if not User.query.filter_by(email="test-admin@freshmart.test").first():
            u = User(name="Test Admin", email="test-admin@freshmart.test", role_id=role.id)
            u.set_password("AdminPass@123")
            _db.session.add(u)
            _db.session.commit()
    return _login(client, "test-admin@freshmart.test", "AdminPass@123")


@pytest.fixture()
def customer_token(app, client):
    with app.app_context():
        from models import User

        if not User.query.filter_by(email="test-customer@freshmart.test").first():
            register_customer(
                name="Test Customer", email="test-customer@freshmart.test",
                password="CustPass@123", address="1 Test St", city="Chennai", pincode="600001",
            )
    return _login(client, "test-customer@freshmart.test", "CustPass@123")


@pytest.fixture()
def sample_category(app, db_session):
    from models import Category

    cat = Category.query.filter_by(name="Test Category").first()
    if not cat:
        cat = Category(name="Test Category", description="For tests")
        db_session.add(cat)
        db_session.commit()
    return cat.id


@pytest.fixture()
def sample_product(app, db_session, sample_category):
    from models import Product, Inventory

    product = Product.query.filter_by(sku="TEST-SKU-01").first()
    if not product:
        product = Product(sku="TEST-SKU-01", name="Test Apples", category_id=sample_category, price=100.0, unit="kg")
        db_session.add(product)
        db_session.flush()
        db_session.add(Inventory(product_id=product.id, quantity=50, reorder_level=5, reorder_quantity=20))
        db_session.commit()
    return product.id
