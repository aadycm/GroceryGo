def register_blueprints(app):
    from routes.auth_routes import bp as auth_bp
    from routes.category_routes import bp as category_bp
    from routes.product_routes import bp as product_bp
    from routes.inventory_routes import bp as inventory_bp
    from routes.order_routes import bp as order_bp
    from routes.payment_routes import bp as payment_bp
    from routes.customer_routes import bp as customer_bp
    from routes.supplier_routes import bp as supplier_bp
    from routes.subscription_routes import bp as subscription_bp
    from routes.branding_routes import bp as branding_bp
    from routes.theme_routes import bp as theme_bp
    from routes.notification_routes import bp as notification_bp
    from routes.report_routes import bp as report_bp
    from routes.audit_routes import bp as audit_bp
    from routes.qr_routes import bp as qr_bp
    from routes.admin_dashboard_routes import bp as admin_dashboard_bp

    for bp in (
        auth_bp, category_bp, product_bp, inventory_bp, order_bp, payment_bp,
        customer_bp, supplier_bp, subscription_bp, branding_bp, theme_bp,
        notification_bp, report_bp, audit_bp, qr_bp, admin_dashboard_bp,
    ):
        app.register_blueprint(bp)
