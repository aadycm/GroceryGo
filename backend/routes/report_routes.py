from flask import Blueprint, request, send_file, g
from models import Order
from models.role import ADMIN, MANAGER
from auth.decorators import token_required, roles_required
from services import report_service
from utils.responses import success, error

bp = Blueprint("reports", __name__, url_prefix="/api/reports")

REPORT_BUILDERS = {
    "sales": lambda period: report_service.sales_report(period),
    "revenue": lambda period: report_service.revenue_report(period),
    "inventory": lambda period: report_service.inventory_report(),
    "customers": lambda period: report_service.customer_report(),
    "top-products": lambda period: report_service.top_products_report(period=period),
}


@bp.get("/<string:report_type>")
@token_required
@roles_required(ADMIN, MANAGER)
def get_report(report_type):
    builder = REPORT_BUILDERS.get(report_type)
    if not builder:
        return error(f"Unknown report type. Choose from {list(REPORT_BUILDERS)}", 404)
    period = request.args.get("period", "monthly")
    if period not in ("daily", "weekly", "monthly"):
        return error("period must be one of: daily, weekly, monthly", 400)
    return success(builder(period))


@bp.get("/<string:report_type>/export")
@token_required
@roles_required(ADMIN, MANAGER)
def export_report(report_type):
    builder = REPORT_BUILDERS.get(report_type)
    if not builder:
        return error(f"Unknown report type. Choose from {list(REPORT_BUILDERS)}", 404)
    period = request.args.get("period", "monthly")
    fmt = request.args.get("format", "pdf")

    data = builder(period)
    rows, columns = _flatten_for_export(report_type, data)
    filename_prefix = f"{report_type}_{period}"

    if fmt == "excel":
        path = report_service.export_report_excel(report_type.title(), rows, columns, filename_prefix)
    else:
        path = report_service.export_report_pdf(report_type.title(), rows, columns, filename_prefix)

    return send_file(path, as_attachment=True)


def _flatten_for_export(report_type, data):
    if report_type == "sales":
        rows = data["orders"]
        columns = ["id", "status", "total_amount", "placed_at"]
    elif report_type == "revenue":
        rows = [{"method": k, "amount": v} for k, v in data["by_method"].items()]
        columns = ["method", "amount"]
    elif report_type == "inventory":
        rows = data["items"]
        columns = ["product_id", "product_name", "quantity", "reorder_level", "is_low_stock"]
    elif report_type == "customers":
        rows = data["customers"]
        columns = ["customer_id", "name", "total_orders", "total_spent", "loyalty_points"]
    else:  # top-products
        rows = data["top_products"]
        columns = ["product_id", "name", "units_sold", "revenue"]
    return rows, columns


@bp.get("/invoice/<int:order_id>")
@token_required
def invoice(order_id):
    order = Order.query.get(order_id)
    if not order:
        return error("Order not found", 404)
    path = report_service.generate_invoice_pdf(order)
    return send_file(path, as_attachment=True)
