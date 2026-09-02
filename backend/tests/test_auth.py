import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./data/test-auth.db"

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_secretary_can_login_and_read_profile() -> None:
    with client:
        response = client.post("/api/auth/login", json={"username": "secretary1", "password": "123456"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["user"]["role"] == "secretary"
        profile = client.get("/api/auth/me", headers={"Authorization": f"Bearer {payload['access_token']}"})
        assert profile.status_code == 200
        assert profile.json()["class_name"] == "23级计算机科学与技术1班"


def test_student_registration_and_role_protection() -> None:
    with client:
        response = client.post("/api/auth/register", json={"username": "test-student", "password": "123456", "display_name": "测试学生", "invite_code": "JSJ23-1"})
        if response.status_code == 409:
            response = client.post("/api/auth/login", json={"username": "test-student", "password": "123456"})
        assert response.status_code == 200 or response.status_code == 201
        token = response.json()["access_token"]
        forbidden = client.get("/api/auth/class-invite", headers={"Authorization": f"Bearer {token}"})
        assert forbidden.status_code == 403


def test_me_requires_token() -> None:
    with client:
        assert client.get("/api/auth/me").status_code == 401
