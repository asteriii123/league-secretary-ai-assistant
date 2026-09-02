from fastapi.testclient import TestClient

from app.main import app


def login(client: TestClient, username: str, password: str = "123456") -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_rag_debug_is_secretary_only_and_returns_full_pipeline(monkeypatch) -> None:
    monkeypatch.setattr("app.routers.rag.retrieve_with_rerank", lambda query, class_id: {
        "vector": [], "bm25": [], "rrf": [],
        "rerank": [{"chunk_id": 1, "rank": 1, "rerank_score": 0.9}],
        "parents": [{"parent_id": 2, "rank": 1, "source_label": "资料1"}],
    })
    with TestClient(app) as client:
        secretary = login(client, "secretary1")
        response = client.post("/api/rag/search/debug", headers={"Authorization": f"Bearer {secretary}"}, json={"query": "团费怎么交"})
        assert response.status_code == 200
        assert response.json()["rerank"][0]["rerank_score"] == 0.9
        assert response.json()["parents"][0]["source_label"] == "资料1"

        register = client.post("/api/auth/register", json={"username": "rag-student", "password": "123456", "display_name": "RAG学生", "invite_code": "JSJ23-1"})
        student = register.json()["access_token"] if register.status_code == 201 else login(client, "rag-student")
        forbidden = client.post("/api/rag/search/debug", headers={"Authorization": f"Bearer {student}"}, json={"query": "团费怎么交"})
        assert forbidden.status_code == 403
