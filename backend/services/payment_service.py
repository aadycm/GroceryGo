import hmac
import hashlib
import secrets
from urllib.parse import quote
from flask import current_app
import razorpay
from database.db import db
from models import Payment, Order
from services.qr_service import generate_payment_qr
from middleware.error_handlers import ApiError


def _client():
    key_id = current_app.config["RAZORPAY_KEY_ID"]
    key_secret = current_app.config["RAZORPAY_KEY_SECRET"]
    if not key_id or not key_secret:
        raise ApiError(
            "Razorpay is not configured. Set RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET.", 503
        )
    return razorpay.Client(auth=(key_id, key_secret))


def create_payment_for_order(order_id, method):
    order = Order.query.get(order_id)
    if not order:
        raise ApiError("Order not found", 404)

    payment = Payment(order_id=order.id, method=method, amount=order.total_amount, status="pending")

    if method == "cash":
        payment.status = "success"
        payment.transaction_ref = f"CASH-{secrets.token_hex(4).upper()}"
        db.session.add(payment)
        db.session.commit()
        return {"payment": payment.to_dict()}

    if method in ("card", "netbanking"):
        client = _client()
        # amount is in the smallest currency unit (paise for INR)
        rzp_order = client.order.create(
            {
                "amount": int(order.total_amount * 100),
                "currency": "INR",
                "receipt": f"order_{order.id}",
                "payment_capture": 1,
            }
        )
        payment.razorpay_order_id = rzp_order["id"]
        db.session.add(payment)
        db.session.commit()
        return {
            "payment": payment.to_dict(),
            "razorpay_key_id": current_app.config["RAZORPAY_KEY_ID"],
            "razorpay_order_id": rzp_order["id"],
            "amount": rzp_order["amount"],
            "currency": rzp_order["currency"],
        }

    if method == "upi":
        vpa = current_app.config["UPI_MERCHANT_VPA"]
        merchant = current_app.config["UPI_MERCHANT_NAME"]
        if not vpa:
            raise ApiError("UPI merchant VPA is not configured (UPI_MERCHANT_VPA).", 503)
        db.session.add(payment)
        db.session.flush()

        upi_link = (
            f"upi://pay?pa={quote(vpa)}&pn={quote(merchant)}"
            f"&am={order.total_amount}&cu=INR&tr=order{order.id}"
        )
        # Single-use, short-lived token so the generated QR cannot be replayed
        # against a different payment; validated in verify_upi_payment().
        token = secrets.token_urlsafe(24)
        payment.transaction_ref = token
        qr_path = generate_payment_qr(payment.id, upi_link, token)
        db.session.commit()
        return {"payment": payment.to_dict(), "upi_link": upi_link, "qr_code_path": qr_path}

    raise ApiError(f"Unsupported payment method: {method}", 400)


def verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    key_secret = current_app.config["RAZORPAY_KEY_SECRET"]
    payload = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected_signature = hmac.new(
        key_secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, razorpay_signature)


def confirm_card_or_netbanking_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    payment = Payment.query.filter_by(razorpay_order_id=razorpay_order_id).first()
    if not payment:
        raise ApiError("Payment record not found for this Razorpay order", 404)

    # Idempotency: if already marked success for this payment id, short-circuit.
    if payment.status == "success" and payment.razorpay_payment_id == razorpay_payment_id:
        return payment

    if not verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
        payment.status = "failed"
        db.session.commit()
        raise ApiError("Payment signature verification failed", 400)

    payment.razorpay_payment_id = razorpay_payment_id
    payment.razorpay_signature = razorpay_signature
    payment.status = "success"
    db.session.commit()
    return payment


def verify_upi_payment(payment_id, token, transaction_ref):
    payment = Payment.query.get(payment_id)
    if not payment:
        raise ApiError("Payment not found", 404)

    # Check the idempotent shortcut BEFORE validating the token: once a
    # payment succeeds we overwrite transaction_ref with the bank's real
    # reference, so the original QR token would no longer match on a
    # legitimate retried callback. A second identical confirmation must
    # succeed, not be rejected as an invalid/expired token.
    if payment.status == "success":
        return payment

    if payment.transaction_ref != token:
        raise ApiError("Invalid or expired QR token for this payment", 400)

    payment.status = "success"
    payment.transaction_ref = transaction_ref
    db.session.commit()
    return payment


def verify_webhook_signature(raw_body, signature, webhook_secret):
    expected = hmac.new(webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
