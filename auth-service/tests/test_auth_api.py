import pytest

TEST_USER = {
    "username": "testuser",
    "password": "testpass123",
    "email": "testuser@example.com",
}

@pytest.fixture()
def access_token(client):
    # register: 201 veya tekrar koşumda 409
    r = client.post("/register", json=TEST_USER)
    assert r.status_code in (201, 409)

    # login
    r2 = client.post("/login", json={
        "username": TEST_USER["username"],
        "password": TEST_USER["password"],
    })
    assert r2.status_code == 200
    data = r2.json()
    assert "access_token" in data
    return data["access_token"]

def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_register_user(client):
    r = client.post("/register", json=TEST_USER)
    assert r.status_code in (201, 409)
    assert "username" in r.json()

def test_login_returns_token(client, access_token):
    # access_token fixture zaten register + login yapıyor
    assert isinstance(access_token, str) and len(access_token) > 10


def test_verify_token(client, access_token):
    r = client.get("/verify", params={"token": access_token})
    assert r.status_code == 200
    assert r.json()["valid"] is True

def test_me_endpoint(client, access_token):
    r = client.get("/me", headers={"Authorization": f"Bearer {access_token}"})
    assert r.status_code == 200
    assert r.json()["username"] == TEST_USER["username"]
