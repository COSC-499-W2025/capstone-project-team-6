from fastapi.testclient import TestClient
from src.backend.main import app

client = TestClient(app)
def test_login_success():
    res = client.post("/login", json={"username": "testuser", "password": "password123"})
    assert res.status_code == 200
    assert res.json()["message"] == "Login successful"


def test_login_failure():
    res = client.post("/login", json={"username": "wrong", "password": "bad"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid username or password"

