from fastapi.testclient import TestClient

from app.rag.documents import Block, PARENT_MAX, SMALL_MAX, build_parent_chunks, build_small_chunks
from app.main import app


def login(client: TestClient, username: str, password: str = "123456") -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def student_token(client: TestClient) -> str:
    response = client.post("/api/auth/register", json={"username": "knowledge-student", "password": "123456", "display_name": "知识测试学生", "invite_code": "JSJ23-1"})
    return login(client, "knowledge-student") if response.status_code == 409 else response.json()["access_token"]


def long_text() -> str:
    return "".join(f"这是第{index}条团务知识资料，用于验证知识资料的Small-to-Big父子分块逻辑是否能够正确切分并保留标题、页码和章节路径信息。" for index in range(120))


def test_small_to_big_chunking() -> None:
    blocks = [Block("heading", "第一章 团务基础", level=1, page=1), Block("paragraph", long_text(), page=1)]
    parents = build_parent_chunks(blocks)
    assert parents, "应生成至少一个父块"
    for parent in parents:
        assert len(parent["content"]) <= PARENT_MAX
    smalls: list[str] = []
    for parent in parents:
        for small in build_small_chunks(parent["content"]):
            assert len(small) <= SMALL_MAX
            smalls.append(small)
    assert len(smalls) >= len(parents)


def test_knowledge_upload_and_parent_child_relation() -> None:
    with TestClient(app) as client:
        secretary = login(client, "secretary1")
        created = client.post("/api/knowledge", headers=auth(secretary), files={"file": ("团务知识.txt", long_text().encode("utf-8"), "text/plain")})
        assert created.status_code == 201, created.text
        document_id = created.json()["id"]
        detail = client.get(f"/api/knowledge/{document_id}", headers=auth(secretary)).json()
        assert detail["status"] == "done", detail.get("error_message")
        assert detail["parent_count"] >= 1
        assert detail["small_count"] >= detail["parent_count"]
        assert detail["parents"], "应返回父块列表"
        for parent in detail["parents"]:
            assert parent["id"] > 0
            assert parent["smalls"], "每个父块下应有小块"
            assert all(small["char_count"] <= SMALL_MAX for small in parent["smalls"])
        client.delete(f"/api/knowledge/{document_id}", headers=auth(secretary))


def test_duplicate_upload_rejected() -> None:
    with TestClient(app) as client:
        secretary = login(client, "secretary1")
        content = long_text().encode("utf-8")
        first = client.post("/api/knowledge", headers=auth(secretary), files={"file": ("重复资料.txt", content, "text/plain")})
        assert first.status_code == 201
        second = client.post("/api/knowledge", headers=auth(secretary), files={"file": ("重复资料2.txt", content, "text/plain")})
        assert second.status_code == 409
        client.delete(f"/api/knowledge/{first.json()['id']}", headers=auth(secretary))


def test_failed_task_can_retry(monkeypatch) -> None:
    from app.rag import documents as knowledge

    original = knowledge.extract_blocks
    monkeypatch.setattr(knowledge, "extract_blocks", lambda source, file_type: (_ for _ in ()).throw(knowledge.KnowledgeError("模拟解析失败")))
    with TestClient(app) as client:
        secretary = login(client, "secretary1")
        created = client.post("/api/knowledge", headers=auth(secretary), files={"file": ("失败资料.txt", long_text().encode("utf-8"), "text/plain")})
        assert created.status_code == 201
        document_id = created.json()["id"]
        assert client.get(f"/api/knowledge/{document_id}", headers=auth(secretary)).json()["status"] == "failed"
    monkeypatch.setattr(knowledge, "extract_blocks", original)
    with TestClient(app) as client:
        secretary = login(client, "secretary1")
        retried = client.post(f"/api/knowledge/{document_id}/retry", headers=auth(secretary))
        assert retried.status_code == 200
        detail = client.get(f"/api/knowledge/{document_id}", headers=auth(secretary)).json()
        assert detail["status"] == "done", detail.get("error_message")
        client.delete(f"/api/knowledge/{document_id}", headers=auth(secretary))


def test_student_cannot_upload() -> None:
    with TestClient(app) as client:
        student = student_token(client)
        response = client.post("/api/knowledge", headers=auth(student), files={"file": ("资料.txt", long_text().encode("utf-8"), "text/plain")})
        assert response.status_code == 403
