def test_register_and_login_customer(client):
    res = client.post("/api/auth/register", json={
        "name": "Jane Doe", "email": "jane@example.com", "password": "SecurePass1",
    })
    assert res.status_code == 201
    assert res.get_json()["data"]["email"] == "jane@example.com"

    res = client.post("/api/auth/login", json={"email": "jane@example.com", "password": "SecurePass1"})
    assert res.status_code == 200
    body = res.get_json()["data"]
    assert "access_token" in body and "refresh_token" in body
    assert body["user"]["role"] == "customer"


def test_login_wrong_password_rejected(client):
    client.post("/api/auth/register", json={
        "name": "Bob", "email": "bob@example.com", "password": "SecurePass1",
    })
    res = client.post("/api/auth/login", json={"email": "bob@example.com", "password": "WrongPass"})
    assert res.status_code == 401


def test_duplicate_registration_rejected(client):
    payload = {"name": "Dup", "email": "dup@example.com", "password": "SecurePass1"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409


def test_protected_route_requires_token(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_me_returns_current_user(client, customer_token):
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {customer_token}"})
    assert res.status_code == 200
    assert res.get_json()["data"]["role"] == "customer"


def test_admin_login_and_role(client, admin_token):
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.get_json()["data"]["role"] == "admin"


def test_refresh_token_issues_new_access_token(client, customer_token):
    res = client.post("/api/auth/login", json={"email": "test-customer@freshmart.test", "password": "CustPass@123"})
    refresh_token = res.get_json()["data"]["refresh_token"]
    res = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    assert "access_token" in res.get_json()["data"]
