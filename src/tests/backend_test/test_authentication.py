# from fastapi.testclient import TestClient
# import pytest

# from src.backend import database
# from src.backend.main import app


# @pytest.fixture
# def client(tmp_path):
#     previous = database.set_db_path(tmp_path / "auth.db")
#     database.reset_db()
#     with TestClient(app) as test_client:
#         yield test_client
#     database.set_db_path(previous)


# def test_login_success(client):
#     res = client.post(
#         "/login", json={"username": "testuser", "password": "password123"}
#     )
#     assert res.status_code == 200
#     assert res.json()["message"] == "Login successful"


# def test_login_failure(client):
#     res = client.post("/login", json={"username": "wrong", "password": "bad"})
#     assert res.status_code == 401
#     assert res.json()["detail"] == "Invalid username or password"


# def test_signup_success(client):
#     payload = {"username": "newuser", "password": "newpass"}
#     res = client.post("/signup", json=payload)
#     assert res.status_code == 200
#     assert res.json()["message"] == "Signup successful"

#     login_res = client.post("/login", json=payload)
#     assert login_res.status_code == 200
#     assert login_res.json()["message"] == "Login successful"


# def test_signup_existing_user(client):
#     payload = {"username": "testuser", "password": "password123"}
#     res = client.post("/signup", json=payload)
#     assert res.status_code == 400
#     assert res.json()["detail"] == "Username already exists"
