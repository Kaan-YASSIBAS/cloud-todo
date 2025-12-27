from fastapi.testclient import TestClient
from app import app

#====================================#
# fastapi.testclient
#====================================#

# TestClient -> It is used to simulate requests to the FastAPI application for testing purposes.

#====================================#
# app
#====================================#

# app -> This is the FastAPI application instance defined in app.py.

#====================================#
# Test Cases
#====================================#

client = TestClient(app)

def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
