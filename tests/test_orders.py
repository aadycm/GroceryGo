def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_customer_can_place_order(client, customer_token, sample_product):
    res = client.post(
        "/api/orders", headers=auth(customer_token),
        json={"items": [{"product_id": sample_product, "quantity": 2}], "delivery_address": "42 Test Rd"},
    )
    assert res.status_code == 201
    order = res.get_json()["data"]
    assert order["status"] == "pending"
    assert order["total_amount"] == 200.0  # 2 * price(100)


def test_cannot_order_more_than_stock(client, customer_token, sample_product):
    res = client.post(
        "/api/orders", headers=auth(customer_token),
        json={"items": [{"product_id": sample_product, "quantity": 999999}], "delivery_address": "42 Test Rd"},
    )
    assert res.status_code == 409


def test_order_requires_items(client, customer_token):
    res = client.post("/api/orders", headers=auth(customer_token), json={"delivery_address": "x"})
    assert res.status_code == 400


def test_customer_sees_only_own_orders(client, customer_token, admin_token, sample_product):
    client.post(
        "/api/orders", headers=auth(customer_token),
        json={"items": [{"product_id": sample_product, "quantity": 1}], "delivery_address": "A"},
    )
    res = client.get("/api/orders", headers=auth(customer_token))
    assert res.status_code == 200
    assert all("id" in o for o in res.get_json()["data"])


def test_admin_can_advance_order_status(client, customer_token, admin_token, sample_product):
    res = client.post(
        "/api/orders", headers=auth(customer_token),
        json={"items": [{"product_id": sample_product, "quantity": 1}], "delivery_address": "A"},
    )
    order_id = res.get_json()["data"]["id"]

    res = client.put(f"/api/orders/{order_id}/status", headers=auth(admin_token), json={"status": "confirmed"})
    assert res.status_code == 200
    assert res.get_json()["data"]["status"] == "confirmed"

    # invalid transition (confirmed -> delivered skips steps) should fail
    res = client.put(f"/api/orders/{order_id}/status", headers=auth(admin_token), json={"status": "delivered"})
    assert res.status_code == 409


def test_cancel_order_restores_stock(client, customer_token, admin_token, sample_product):
    inv_before = client.get("/api/inventory", headers=auth(admin_token)).get_json()["data"]
    qty_before = next(i["quantity"] for i in inv_before if i["product_id"] == sample_product)

    res = client.post(
        "/api/orders", headers=auth(customer_token),
        json={"items": [{"product_id": sample_product, "quantity": 3}], "delivery_address": "A"},
    )
    order_id = res.get_json()["data"]["id"]

    client.post(f"/api/orders/{order_id}/cancel", headers=auth(customer_token))

    inv_after = client.get("/api/inventory", headers=auth(admin_token)).get_json()["data"]
    qty_after = next(i["quantity"] for i in inv_after if i["product_id"] == sample_product)
    assert qty_after == qty_before


def test_order_tracking_endpoint(client, customer_token, sample_product):
    res = client.post(
        "/api/orders", headers=auth(customer_token),
        json={"items": [{"product_id": sample_product, "quantity": 1}], "delivery_address": "A"},
    )
    order_id = res.get_json()["data"]["id"]
    res = client.get(f"/api/orders/{order_id}/track", headers=auth(customer_token))
    assert res.status_code == 200
    assert res.get_json()["data"]["status"] == "pending"
