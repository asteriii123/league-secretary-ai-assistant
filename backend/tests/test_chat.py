from fastapi.testclient import TestClient

from app.ai import get_deepseek_client
from app.main import app


class FakeStreamingClient:
    async def stream(self, messages: list[dict[str, str]]):
        assert messages[0]["role"] == "system"
        yield "这是"
        yield "测试回答"


def secretary_token(client: TestClient) -> str:
    response = client.post("/api/auth/login", json={"username": "secretary1", "password": "123456"})
    return response.json()["access_token"]


def test_chat_stream_requires_login() -> None:
    with TestClient(app) as client:
        response = client.post("/api/ai/chat/stream", json={"question": "请介绍团员义务", "history": []})
        assert response.status_code == 401


def test_chat_stream_returns_sse_content() -> None:
    app.dependency_overrides[get_deepseek_client] = lambda: FakeStreamingClient()
    try:
        with TestClient(app) as client:
            token = secretary_token(client)
            response = client.post("/api/ai/chat/stream", headers={"Authorization": f"Bearer {token}"}, json={"question": "请帮我起草通知", "history": []})
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            assert "event: status" in response.text
            assert 'data: {"text": "这是"}' in response.text
            assert "event: done" in response.text
    finally:
        app.dependency_overrides.clear()


def test_chat_rejects_too_many_history_messages() -> None:
    with TestClient(app) as client:
        token = secretary_token(client)
        history = [{"role": "user", "content": "问题"}] * 13
        response = client.post("/api/ai/chat/stream", headers={"Authorization": f"Bearer {token}"}, json={"question": "继续回答", "history": history})
        assert response.status_code == 422
