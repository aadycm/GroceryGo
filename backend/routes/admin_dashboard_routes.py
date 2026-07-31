"""Server-rendered admin dashboard shell. Pages are static Jinja2 templates
that fetch live data client-side from the /api/* endpoints using the JWT
stored after login (see admin-dashboard/static/js/dashboard.js). This keeps a
single source of truth (the REST API) for both the customer app and the
admin dashboard, instead of duplicating query logic in server-rendered views.
"""
from flask import Blueprint, render_template

bp = Blueprint("admin_dashboard", __name__, url_prefix="/admin")

PAGES = [
    "dashboard", "inventory", "customers", "orders", "reports", "payments",
    "branding", "theme", "subscriptions", "settings", "analytics",
]


@bp.get("/")
@bp.get("/login")
def login_page():
    return render_template("login.html")


for _page in PAGES:
    def _make_view(page_name):
        def _view():
            return render_template(f"{page_name}.html", active_page=page_name)
        _view.__name__ = f"{page_name}_page"
        return _view

    bp.add_url_rule(f"/{_page}", view_func=_make_view(_page))
