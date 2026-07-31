"""Seeds roles, demo users (Owner/Auditor/Staff/Delivery/Customer), categories,
products with inventory, a supplier, branding + theme defaults, and one sample
order — enough to exercise every module end-to-end.

Usage: python seed.py
"""
from datetime import date, timedelta
from app import create_app
from database.db import db
from models import (
    Role, User, Customer, Category, Product, Supplier, Inventory,
    BrandingSettings, ThemeSettings, Subscription,
)
from models.role import ALL_ROLES, ADMIN, MANAGER, STAFF, DELIVERY, CUSTOMER
from services.order_service import create_order

app = create_app()


def run():
    with app.app_context():
        db.create_all()

        roles = {}
        for name in ALL_ROLES:
            role = Role.query.filter_by(name=name).first()
            if not role:
                role = Role(name=name, description=name.capitalize())
                db.session.add(role)
                db.session.flush()
            roles[name] = role
        db.session.commit()

        def get_or_create_user(name, email, password, role_name, phone=None):
            user = User.query.filter_by(email=email).first()
            if user:
                return user
            user = User(name=name, email=email, phone=phone, role_id=roles[role_name].id)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()
            return user

        owner = get_or_create_user("Priya Nair", "owner@freshmart.test", "Owner@12345", ADMIN, "9840000001")
        auditor = get_or_create_user("Deepak Srinivas", "auditor@freshmart.test", "Auditor@12345", MANAGER, "9840000002")
        staff = get_or_create_user("Anjali Mehta", "staff@freshmart.test", "Staff@12345", STAFF, "9840000003")
        rider = get_or_create_user("Karthik Raja", "delivery@freshmart.test", "Delivery@12345", DELIVERY, "9840000004")
        cust_user = get_or_create_user("Vaidhy Kumar", "customer@freshmart.test", "Customer@12345", CUSTOMER, "9840000005")
        db.session.commit()

        customer = Customer.query.filter_by(user_id=cust_user.id).first()
        if not customer:
            customer = Customer(
                user_id=cust_user.id, address="12 Nandambakkam Main Rd", city="Chennai", pincode="600089"
            )
            db.session.add(customer)
            db.session.commit()

        supplier = Supplier.query.filter_by(name="Chennai Fresh Wholesalers").first()
        if not supplier:
            supplier = Supplier(
                name="Chennai Fresh Wholesalers", contact_person="Ramesh Kumar",
                phone="9845012345", email="ramesh@cfwholesale.test", address="Koyambedu Market, Chennai",
            )
            db.session.add(supplier)
            db.session.commit()

        categories_data = [
            ("Vegetables", "Fresh farm vegetables"),
            ("Fruits", "Seasonal fresh fruits"),
            ("Dairy", "Milk, curd, paneer and more"),
            ("Bakery", "Bread, buns, and baked goods"),
            ("Beverages", "Juices, soft drinks, water"),
        ]
        categories = {}
        for name, desc in categories_data:
            cat = Category.query.filter_by(name=name).first()
            if not cat:
                cat = Category(name=name, description=desc)
                db.session.add(cat)
                db.session.flush()
            categories[name] = cat
        db.session.commit()

        products_data = [
            ("VEG-TOM-01", "Tomato", "Vegetables", 30.0, "kg", 100),
            ("VEG-ONI-01", "Onion", "Vegetables", 35.0, "kg", 120),
            ("VEG-POT-01", "Potato", "Vegetables", 28.0, "kg", 150),
            ("FRT-BAN-01", "Banana", "Fruits", 45.0, "dozen", 60),
            ("FRT-APP-01", "Apple (Shimla)", "Fruits", 180.0, "kg", 40),
            ("DAI-MLK-01", "Toned Milk", "Dairy", 27.0, "litre", 80),
            ("DAI-CRD-01", "Curd", "Dairy", 40.0, "pack", 50),
            ("BAK-BRD-01", "Whole Wheat Bread", "Bakery", 45.0, "pack", 5),
            ("BEV-JUC-01", "Orange Juice 1L", "Beverages", 110.0, "pack", 30),
        ]
        for sku, name, cat_name, price, unit, qty in products_data:
            product = Product.query.filter_by(sku=sku).first()
            if not product:
                product = Product(
                    sku=sku, name=name, category_id=categories[cat_name].id, price=price, unit=unit,
                    description=f"{name} - farm fresh, sourced daily.",
                )
                db.session.add(product)
                db.session.flush()
                db.session.add(
                    Inventory(
                        product_id=product.id, quantity=qty, reorder_level=10,
                        reorder_quantity=100, supplier_id=supplier.id,
                    )
                )
        db.session.commit()

        if not BrandingSettings.query.first():
            db.session.add(
                BrandingSettings(
                    app_name="FreshMart", primary_color="#2E7D32", secondary_color="#FFC107"
                )
            )
        if not ThemeSettings.query.first():
            db.session.add(ThemeSettings(theme_name="light", colors={}, is_active=True))
            db.session.add(ThemeSettings(theme_name="dark", colors={}, is_active=False))
        db.session.commit()

        if not Subscription.query.filter_by(customer_id=customer.id).first():
            db.session.add(
                Subscription(
                    customer_id=customer.id, plan_name="FreshMart Plus - Monthly",
                    status="active", start_date=date.today(),
                    end_date=date.today() + timedelta(days=30), amount=199.0,
                )
            )
            db.session.commit()

        if not customer.orders:
            tomato = Product.query.filter_by(sku="VEG-TOM-01").first()
            milk = Product.query.filter_by(sku="DAI-MLK-01").first()
            create_order(
                customer.id,
                [
                    {"product_id": tomato.id, "quantity": 2},
                    {"product_id": milk.id, "quantity": 3},
                ],
                delivery_address=customer.address,
                user_id=cust_user.id,
            )

        print("Seed complete.")
        print("Demo logins (email / password):")
        print("  Owner   : owner@freshmart.test / Owner@12345")
        print("  Auditor : auditor@freshmart.test / Auditor@12345")
        print("  Staff   : staff@freshmart.test / Staff@12345")
        print("  Delivery: delivery@freshmart.test / Delivery@12345")
        print("  Customer: customer@freshmart.test / Customer@12345")


if __name__ == "__main__":
    run()
