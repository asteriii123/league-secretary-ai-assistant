from fastapi.testclient import TestClient

from app.llm.deepseek import get_deepseek_client
from app.main import app


class FakeStreamingClient:
    calls: list[list[dict[str, str]]] = []

    async def stream(self, messages: list[dict[str, str]]):
        self.calls.append(messages)
        yield "# 标题\n\n* 第一项"


def login(client: TestClient, username: str) -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": "123456"})
    assert response.status_code == 200
    return response.json()["access_token"]


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_conversation_history_is_private_and_persistent(monkeypatch) -> None:
    fake = FakeStreamingClient(); fake.calls = []
    monkeypatch.setattr("app.api.routers.conversations.retrieve_with_rerank", lambda *_: {"parents": []})
    app.dependency_overrides[get_deepseek_client] = lambda: fake
    try:
        with TestClient(app) as client:
            owner = login(client, "secretary1"); other = login(client, "secretary2")
            created = client.post("/api/ai/conversations", headers=headers(owner))
            assert created.status_code == 201
            conversation_id = created.json()["id"]
            first = client.post(f"/api/ai/conversations/{conversation_id}/messages/stream", headers=headers(owner), json={"question": "第一轮问题"})
            second = client.post(f"/api/ai/conversations/{conversation_id}/messages/stream", headers=headers(owner), json={"question": "继续说明上一轮"})
            assert first.status_code == 200 and second.status_code == 200
            saved = client.get(f"/api/ai/conversations/{conversation_id}/messages", headers=headers(owner))
            assert [item["role"] for item in saved.json()] == ["user", "assistant", "user", "assistant"]
            assert fake.calls[-1][-2]["content"] == "# 标题\n\n* 第一项"
            assert client.get(f"/api/ai/conversations/{conversation_id}/messages", headers=headers(other)).status_code == 404
            assert client.delete(f"/api/ai/conversations/{conversation_id}", headers=headers(owner)).status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_student_can_create_unified_conversation() -> None:
    with TestClient(app) as client:
        register = client.post("/api/auth/register", json={"username": "conversation-student", "password": "123456", "display_name": "对话学生", "invite_code": "JSJ23-1"})
        token = register.json()["access_token"] if register.status_code == 201 else login(client, "conversation-student")
        response = client.post("/api/ai/conversations", headers=headers(token))
        assert response.status_code == 201


def test_casual_message_skips_rag_and_has_no_sources(monkeypatch) -> None:
    fake = FakeStreamingClient(); fake.calls = []
    def unexpected_retrieval(*_):
        raise AssertionError("寒暄消息不应调用RAG")
    monkeypatch.setattr("app.api.routers.conversations.retrieve_with_rerank", unexpected_retrieval)
    app.dependency_overrides[get_deepseek_client] = lambda: fake
    try:
        with TestClient(app) as client:
            token = login(client, "secretary1")
            conversation = client.post("/api/ai/conversations", headers=headers(token)).json()
            response = client.post(
                f"/api/ai/conversations/{conversation['id']}/messages/stream",
                headers=headers(token), json={"question": "你好"},
            )
            assert response.status_code == 200
            assert "event: sources" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_only_relevant_rag_results_are_cited(monkeypatch) -> None:
    fake = FakeStreamingClient(); fake.calls = []
    result = {"parents": [{
        "source_label": "资料1", "filename": "团务手册.pdf", "section_path": "团费",
        "heading": "团费", "page": 2, "content": "团费缴纳说明", "rerank_score": 0.1,
    }]}
    monkeypatch.setattr("app.api.routers.conversations.retrieve_with_rerank", lambda *_: result)
    app.dependency_overrides[get_deepseek_client] = lambda: fake
    try:
        with TestClient(app) as client:
            token = login(client, "secretary1")
            conversation = client.post("/api/ai/conversations", headers=headers(token)).json()
            low = client.post(
                f"/api/ai/conversations/{conversation['id']}/messages/stream",
                headers=headers(token), json={"question": "今天天气怎么样"},
            )
            assert "event: sources" not in low.text
            result["parents"][0]["rerank_score"] = 0.9
            relevant = client.post(
                f"/api/ai/conversations/{conversation['id']}/messages/stream",
                headers=headers(token), json={"question": "团费应该怎么缴纳"},
            )
            assert "event: sources" in relevant.text
            assert "团务手册.pdf" in relevant.text
    finally:
        app.dependency_overrides.clear()


def test_smart_search_adds_web_sources(monkeypatch) -> None:
    from app.search.service import WebSearchResponse

    fake = FakeStreamingClient(); fake.calls = []

    async def fake_search(_query: str) -> WebSearchResponse:
        return WebSearchResponse(results=[{
            "title": "共青团中央通知", "url": "https://www.gqt.org.cn/test", "snippet": "通知内容",
            "published_at": None, "provider": "tavily", "score": .9,
        }], warnings=[])

    monkeypatch.setattr("app.api.routers.conversations.retrieve_with_rerank", lambda *_: {"parents": []})
    monkeypatch.setattr("app.api.routers.conversations.search_web", fake_search)
    app.dependency_overrides[get_deepseek_client] = lambda: fake
    try:
        with TestClient(app) as client:
            token = login(client, "secretary1")
            conversation = client.post("/api/ai/conversations", headers=headers(token)).json()
            response = client.post(
                f"/api/ai/conversations/{conversation['id']}/messages/stream",
                headers=headers(token), json={"question": "查询最新团务通知", "web_search_enabled": True},
            )
            assert '"type": "web"' in response.text
            assert "共青团中央通知" in response.text
            assert "[网页1]" in fake.calls[-1][0]["content"]
    finally:
        app.dependency_overrides.clear()
