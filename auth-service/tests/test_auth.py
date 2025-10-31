from fastapi.testclient import TestClient
from app import app  # Import your FastAPI app
import jwt

#====================================#
# fastapi.testclient
#====================================#

# TestClient -> It is used to simulate requests to the FastAPI application for testing purposes.

#====================================#
# app
#====================================#

# app -> This is the FastAPI application instance defined in app.py.

#====================================#
# jwt
#====================================#

# jwt -> It is used for encoding and decoding JSON Web Tokens (JWT).

#====================================#
# Test Cases
#====================================#


client = TestClient(app)

# Test user credentials
TEST_USER = {
    "username": "testuser",
    "password": "testpass123",
    "email": "testuser@example.com"
}


def test_healthz():
    """Check if the service is running"""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_user():
    """Register a new user"""
    response = client.post("/register", json=TEST_USER)

    # 201 → Created, 409 → Already exists (if test runs multiple times)
    assert response.status_code in (201, 409)
    data = response.json()
    assert "username" in data


def test_login_user():
    """Login with existing user and retrieve JWT token"""
    response = client.post("/login", json={
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    global ACCESS_TOKEN
    ACCESS_TOKEN = data["access_token"]


def test_verify_token():
    """Verify that the returned JWT token is valid"""
    token = ACCESS_TOKEN
    response = client.get(f"/verify?token={token}")
    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_me_endpoint():
    """Access /me endpoint using the JWT token"""
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    response = client.get("/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == TEST_USER["username"]
