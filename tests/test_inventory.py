def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_customer_cannot_access_inventory(client, customer_token):
    res = client.get("/api/inventory", headers=auth(customer_token))
    assert res.status_code == 403


def test_admin_can_list_inventory(client, admin_token, sample_product):
    res = client.get("/api/inventory", headers=auth(admin_token))
    assert res.status_code == 200
    assert any(i["product_id"] == sample_product for i in res.get_json()["data"])


def test_restock_increases_quantity(client, admin_token, sample_product):
    before = client.get("/api/inventory", headers=auth(admin_token)).get_json()["data"]
    qty_before = next(i["quantity"] for i in before if i["product_id"] == sample_product)

    res = client.post(
        f"/api/inventory/{sample_product}/adjust",
        headers=auth(admin_token),
        json={"change_qty": 15, "reason": "restock"},
    )
    assert res.status_code == 200
    assert res.get_json()["data"]["quantity"] == qty_before + 15


def test_adjust_below_zero_rejected(client, admin_token, sample_product):
    res = client.post(
        f"/api/inventory/{sample_product}/adjust",
        headers=auth(admin_token),
        json={"change_qty": -100000, "reason": "adjustment"},
    )
    assert res.status_code == 409


def test_low_stock_endpoint(client, admin_token, sample_product):
    client.put(f"/api/inventory/{sample_product}", headers=auth(admin_token), json={"reorder_level": 100000})
    res = client.get("/api/inventory/low-stock", headers=auth(admin_token))
    assert res.status_code == 200
    assert any(i["product_id"] == sample_product for i in res.get_json()["data"])


def test_reorder_suggestions_endpoint(client, admin_token, sample_product):
    res = client.get("/api/inventory/reorder-suggestions", headers=auth(admin_token))
    assert res.status_code == 200
    assert isinstance(res.get_json()["data"], list)


def test_inventory_history_recorded(client, admin_token, sample_product):
    client.post(f"/api/inventory/{sample_product}/adjust", headers=auth(admin_token), json={"change_qty": 5, "reason": "restock"})
    res = client.get(f"/api/inventory/{sample_product}/history", headers=auth(admin_token))
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 1
