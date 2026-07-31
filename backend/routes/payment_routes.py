from flask import Blueprint, request, g, current_app
from models import Order, Customer
from models.payment import PAYMENT_METHODS
from models.role import CUSTOMER, ADMIN, MANAGER
from auth.decorators import token_required, roles_required
from services.payment_service import (
    create_payment_for_order,
    confirm_card_or_netbanking_payment,
    verify_upi_payment,
    verify_webhook_signature,
)
from services.order_service import update_order_status
from utils.responses import success, error
from utils.validators import require_fields
from middleware.error_handlers import ApiError

bp = Blueprint("payments", __name__, url_prefix="/api/payments")


@bp.post("/orders/<int:order_id>/initiate")
@token_required
def initiate(order_id):
    payload = request.get_json(silent=True) or {}
    method = payload.get("method")
    if method not in PAYMENT_METHODS:
        return error(f"method must be one of {PAYMENT_METHODS}", 400)

    order = Order.query.get(order_id)
    if not order:
        return error("Order not found", 404)

    user = g.current_user
    if user.role.name == CUSTOMER:
        customer = Customer.query.filter_by(user_id=user.id).first()
        if not customer or order.customer_id != customer.id:
            return error("Forbidden", 403)

    result = create_payment_for_order(order_id, method)
    return success(result, "Payment initiated", 201)


@bp.post("/razorpay/verify")
@token_required
def verify_razorpay():
    payload = request.get_json(silent=True) or {}
    missing = require_fields(
        payload, ["razorpay_order_id", "razorpay_payment_id", "razorpay_signature"]
    )
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 400)

    payment = confirm_card_or_netbanking_payment(
        payload["razorpay_order_id"], payload["razorpay_payment_id"], payload["razorpay_signature"]
    )
    # Only advance the order the first time payment succeeds. Verification
    # callbacks can be retried by the client/gateway; if the order has
    # already moved past 'pending' this is a no-op, not a conflict.
    order = Order.query.get(payment.order_id)
    if order and order.status == "pending":
        update_order_status(payment.order_id, "confirmed", user_id=g.current_user.id)
    return success(payment.to_dict(), "Payment verified")


@bp.post("/upi/verify")
@token_required
def verify_upi():
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["payment_id", "token", "transaction_ref"])
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 400)

    payment = verify_upi_payment(payload["payment_id"], payload["token"], payload["transaction_ref"])
    order = Order.query.get(payment.order_id)
    if order and order.status == "pending":
        update_order_status(payment.order_id, "confirmed", user_id=g.current_user.id)
    return success(payment.to_dict(), "UPI payment verified")


@bp.post("/razorpay/webhook")
def razorpay_webhook():
    signature = request.headers.get("X-Razorpay-Signature", "")
    secret = current_app.config["RAZORPAY_WEBHOOK_SECRET"]
    if not secret:
        return error("Webhook secret not configured", 503)
    if not verify_webhook_signature(request.get_data(), signature, secret):
        return error("Invalid webhook signature", 400)
    # Payload processing intentionally minimal: acknowledge receipt. Payment
    # status is authoritatively set via /razorpay/verify using the signed
    # response Razorpay returns to the client checkout flow.
    return success(None, "Webhook received")


@bp.get("/order/<int:order_id>")
@token_required
def payments_for_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return error("Order not found", 404)
    return success([p.to_dict() for p in order.payments])
