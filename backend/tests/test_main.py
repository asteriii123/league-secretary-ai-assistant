from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_welcome_secretary() -> None:
    response = client.get("/api/welcome", params={"role": "secretary"})
    assert response.status_code == 200
    assert response.json() == {
        "message": "你好，团支书！前端已经成功连接 FastAPI。",
        "role": "secretary",
    }


def test_welcome_student() -> None:
    response = client.get("/api/welcome", params={"role": "student"})
    assert response.status_code == 200
    assert response.json()["role"] == "student"


def test_welcome_rejects_invalid_role() -> None:
    response = client.get("/api/welcome", params={"role": "admin"})
    assert response.status_code == 422
