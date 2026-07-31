def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_customer_forbidden_from_reports(client, customer_token):
    res = client.get("/api/reports/sales", headers=auth(customer_token))
    assert res.status_code == 403


def test_sales_report_shape(client, admin_token):
    res = client.get("/api/reports/sales?period=monthly", headers=auth(admin_token))
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "total_orders" in data and "total_revenue" in data


def test_unknown_report_type_404(client, admin_token):
    res = client.get("/api/reports/bogus", headers=auth(admin_token))
    assert res.status_code == 404


def test_inventory_report_pdf_export(client, admin_token):
    res = client.get("/api/reports/inventory/export?format=pdf", headers=auth(admin_token))
    assert res.status_code == 200
    assert res.content_type == "application/pdf"


def test_inventory_report_excel_export(client, admin_token):
    res = client.get("/api/reports/inventory/export?format=excel", headers=auth(admin_token))
    assert res.status_code == 200
    assert len(res.data) > 0


def test_invoice_generation(client, customer_token, sample_product):
    res = client.post(
        "/api/orders", headers=auth(customer_token),
        json={"items": [{"product_id": sample_product, "quantity": 1}], "delivery_address": "A"},
    )
    order_id = res.get_json()["data"]["id"]
    res = client.get(f"/api/reports/invoice/{order_id}", headers=auth(customer_token))
    assert res.status_code == 200
    assert res.content_type == "application/pdf"
