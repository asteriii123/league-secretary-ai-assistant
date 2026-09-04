from fastapi.testclient import TestClient

from app.llm.deepseek import get_deepseek_client
from app.main import app


def login(client: TestClient, username: str, password: str = "123456") -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def student_token(client: TestClient) -> str:
    username = "notice-student"
    response = client.post("/api/auth/register", json={"username": username, "password": "123456", "display_name": "通知测试学生", "invite_code": "JSJ23-1"})
    if response.status_code == 409:
        return login(client, username)
    assert response.status_code == 201
    return response.json()["access_token"]


def test_notice_visibility_read_tracking_and_class_isolation() -> None:
    with TestClient(app) as client:
        secretary = login(client, "secretary1")
        other_secretary = login(client, "secretary2")
        student = student_token(client)
        draft = client.post("/api/notices", headers=auth(secretary), data={"title": "草稿", "content": "暂不发布", "status": "draft"})
        published = client.post("/api/notices", headers=auth(secretary), data={"title": "已发布通知", "content": "请按时完成", "status": "published"})
        assert draft.status_code == 201 and published.status_code == 201
        notice_id = published.json()["id"]
        student_list = client.get("/api/notices", headers=auth(student)).json()
        assert any(item["id"] == notice_id for item in student_list)
        assert all(item["status"] == "published" for item in student_list)
        assert client.post(f"/api/notices/{notice_id}/read", headers=auth(student)).status_code == 200
        readers = client.get(f"/api/notices/{notice_id}/readers", headers=auth(secretary)).json()
        assert any(item["display_name"] == "通知测试学生" for item in readers["read"])
        other_list = client.get("/api/notices", headers=auth(other_secretary)).json()
        assert all(item["id"] != notice_id for item in other_list)


def test_student_cannot_create_notice() -> None:
    with TestClient(app) as client:
        response = client.post("/api/notices", headers=auth(student_token(client)), data={"title": "越权", "content": "不允许", "status": "published"})
        assert response.status_code == 403


def test_notice_attachment_validation() -> None:
    with TestClient(app) as client:
        token = login(client, "secretary1")
        invalid = client.post("/api/notices", headers=auth(token), data={"title": "附件", "content": "测试", "status": "draft"}, files={"attachment": ("script.exe", b"bad", "application/octet-stream")})
        assert invalid.status_code == 400
        valid = client.post("/api/notices", headers=auth(token), data={"title": "附件", "content": "测试", "status": "published"}, files={"attachment": ("notice.pdf", b"%PDF-test", "application/pdf")})
        assert valid.status_code == 201
        notice_id = valid.json()["id"]
        download = client.get(f"/api/notices/{notice_id}/attachment", headers=auth(token))
        assert download.status_code == 200
        assert download.content == b"%PDF-test"


class FakeDraftClient:
    async def complete(self, messages: list[dict[str, str]]) -> str:
        return "标题：团费收缴通知\n请各位同学于【请填写】前完成团费缴纳。"


def test_ai_draft_requires_secretary_and_returns_editable_text() -> None:
    app.dependency_overrides[get_deepseek_client] = lambda: FakeDraftClient()
    try:
        with TestClient(app) as client:
            token = login(client, "secretary1")
            response = client.post("/api/notices/ai-draft", headers=auth(token), json={"topic": "提醒同学缴纳团费"})
            assert response.status_code == 200
            assert response.json()["title"] == "团费收缴通知"
            assert "【请填写】" in response.json()["content"]
    finally:
        app.dependency_overrides.clear()
