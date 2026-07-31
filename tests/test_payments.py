def auth(token):
    return {"Authorization": f"Bearer {token}"}


def _place_order(client, customer_token, sample_product):
    res = client.post(
        "/api/orders", headers=auth(customer_token),
        json={"items": [{"product_id": sample_product, "quantity": 1}], "delivery_address": "A"},
    )
    return res.get_json()["data"]["id"]


def test_cash_payment_succeeds_immediately(client, customer_token, sample_product):
    order_id = _place_order(client, customer_token, sample_product)
    res = client.post(f"/api/payments/orders/{order_id}/initiate", headers=auth(customer_token), json={"method": "cash"})
    assert res.status_code == 201
    assert res.get_json()["data"]["payment"]["status"] == "success"


def test_upi_payment_returns_qr(client, customer_token, sample_product, app):
    order_id = _place_order(client, customer_token, sample_product)
    app.config["UPI_MERCHANT_VPA"] = "test@upi"
    res = client.post(f"/api/payments/orders/{order_id}/initiate", headers=auth(customer_token), json={"method": "upi"})
    assert res.status_code == 201
    data = res.get_json()["data"]
    assert "upi_link" in data
    assert data["payment"]["status"] == "pending"


def test_card_payment_without_razorpay_config_fails_gracefully(client, customer_token, sample_product, app):
    order_id = _place_order(client, customer_token, sample_product)
    app.config["RAZORPAY_KEY_ID"] = ""
    app.config["RAZORPAY_KEY_SECRET"] = ""
    res = client.post(f"/api/payments/orders/{order_id}/initiate", headers=auth(customer_token), json={"method": "card"})
    assert res.status_code == 503  # explicit, clear error rather than a crash


def test_invalid_payment_method_rejected(client, customer_token, sample_product):
    order_id = _place_order(client, customer_token, sample_product)
    res = client.post(f"/api/payments/orders/{order_id}/initiate", headers=auth(customer_token), json={"method": "bitcoin"})
    assert res.status_code == 400


def test_upi_verify_is_idempotent(client, customer_token, sample_product, app):
    order_id = _place_order(client, customer_token, sample_product)
    app.config["UPI_MERCHANT_VPA"] = "test@upi"
    res = client.post(f"/api/payments/orders/{order_id}/initiate", headers=auth(customer_token), json={"method": "upi"})
    data = res.get_json()["data"]
    payment_id = data["payment"]["id"]
    token = data["payment"]["transaction_ref"]

    res1 = client.post("/api/payments/upi/verify", headers=auth(customer_token), json={
        "payment_id": payment_id, "token": token, "transaction_ref": "UPI-REF-1",
    })
    assert res1.status_code == 200
    res2 = client.post("/api/payments/upi/verify", headers=auth(customer_token), json={
        "payment_id": payment_id, "token": token, "transaction_ref": "UPI-REF-1",
    })
    assert res2.status_code == 200  # idempotent, not a duplicate-charge error
