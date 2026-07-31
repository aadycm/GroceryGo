import os
import qrcode
from flask import current_app


def _ensure_folder():
    os.makedirs(current_app.config["QR_FOLDER"], exist_ok=True)


def generate_qr_code(data, filename_prefix, single_use_token=None):
    """Generates a PNG QR code encoding `data` (a string/URL/JSON payload) and
    returns the relative path it was saved to. Used for orders, products, and
    single-use expiring payment QR codes (token embedded by the caller with a
    short expiry, validated server-side on redemption).
    """
    _ensure_folder()
    payload = data if not single_use_token else f"{data}?token={single_use_token}"
    img = qrcode.make(payload)
    filename = f"{filename_prefix}.png"
    path = os.path.join(current_app.config["QR_FOLDER"], filename)
    img.save(path)
    return os.path.join("uploads", "qrcodes", filename)


def generate_order_qr(order_id):
    return generate_qr_code(f"grocerygo://order/{order_id}", f"order_{order_id}")


def generate_product_qr(product_id):
    return generate_qr_code(f"grocerygo://product/{product_id}", f"product_{product_id}")


def generate_payment_qr(payment_id, upi_link, single_use_token):
    return generate_qr_code(
        upi_link, f"payment_{payment_id}", single_use_token=single_use_token
    )
