from fastapi.testclient import TestClient

from app.main import app


FIELDS = [
    {"id": "name", "label": "姓名", "type": "text", "required": True, "options": []},
    {"id": "date", "label": "填写日期", "type": "date", "required": True, "options": []},
    {"id": "choice", "label": "是否参加", "type": "single", "required": True, "options": ["参加", "不参加"]},
]


def login(client: TestClient, username: str, password: str = "123456") -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def student_token(client: TestClient) -> str:
    response = client.post("/api/auth/register", json={"username": "collection-student", "password": "123456", "display_name": "收集测试学生", "invite_code": "JSJ23-1"})
    return login(client, "collection-student") if response.status_code == 409 else response.json()["access_token"]


def create_task(client: TestClient, token: str, **changes) -> dict:
    payload = {"title": "团员信息收集", "description": "请如实填写", "fields": FIELDS, "status": "published", "attachment_required": False, "allow_modify": True}
    payload.update(changes)
    response = client.post("/api/collections", headers=auth(token), json=payload)
    assert response.status_code == 201
    return response.json()


def test_collection_submission_return_resubmit_and_export() -> None:
    with TestClient(app) as client:
        secretary = login(client, "secretary1"); student = student_token(client)
        task = create_task(client, secretary); task_id = task["id"]
        saved = client.put(f"/api/collections/{task_id}/my-submission", headers=auth(student), data={"answers": '{"name":"张三","date":"2026-09-02","choice":"参加"}', "submit": "true"})
        assert saved.status_code == 200 and saved.json()["status"] == "submitted"
        records = client.get(f"/api/collections/{task_id}/submissions", headers=auth(secretary)).json()
        record = next(item for item in records["submissions"] if item["student_name"] == "收集测试学生")
        returned = client.post(f"/api/collections/{task_id}/submissions/{record['id']}/return", headers=auth(secretary), json={"reason": "请修改姓名"})
        assert returned.status_code == 200
        mine = client.get(f"/api/collections/{task_id}/my-submission", headers=auth(student)).json()
        assert mine["status"] == "returned" and mine["return_reason"] == "请修改姓名"
        resubmit = client.put(f"/api/collections/{task_id}/my-submission", headers=auth(student), data={"answers": '{"name":"李四","date":"2026-09-02","choice":"参加"}', "submit": "true"})
        assert resubmit.status_code == 200 and resubmit.json()["return_reason"] is None
        exported = client.get(f"/api/collections/{task_id}/export", headers=auth(secretary))
        assert exported.status_code == 200 and "李四" in exported.content.decode("utf-8-sig")
        client.delete(f"/api/collections/{task_id}", headers=auth(secretary))


def test_collection_permissions_visibility_and_validation() -> None:
    with TestClient(app) as client:
        secretary = login(client, "secretary1"); other = login(client, "secretary2"); student = student_token(client)
        draft = create_task(client, secretary, title="内部草稿", status="draft")
        assert all(item["id"] != draft["id"] for item in client.get("/api/collections", headers=auth(student)).json())
        assert client.patch(f"/api/collections/{draft['id']}", headers=auth(student), json={"title": "越权", "fields": FIELDS}).status_code == 403
        assert client.get(f"/api/collections/{draft['id']}/submissions", headers=auth(other)).status_code == 404
        invalid = client.post("/api/collections", headers=auth(secretary), json={"title": "错误字段", "fields": [{"id": "x", "label": "选择", "type": "single", "options": ["一个"]}]})
        assert invalid.status_code == 400
        client.delete(f"/api/collections/{draft['id']}", headers=auth(secretary))


def test_collection_attachment_validation_and_required_answer() -> None:
    with TestClient(app) as client:
        secretary = login(client, "secretary1"); student = student_token(client)
        task = create_task(client, secretary, attachment_required=True); task_id = task["id"]
        missing = client.put(f"/api/collections/{task_id}/my-submission", headers=auth(student), data={"answers": '{}', "submit": "true"})
        assert missing.status_code == 400
        invalid = client.put(f"/api/collections/{task_id}/my-submission", headers=auth(student), data={"answers": '{"name":"张三","date":"2026-09-02","choice":"参加"}', "submit": "true"}, files={"attachment": ("bad.exe", b"bad", "application/octet-stream")})
        assert invalid.status_code == 400
        valid = client.put(f"/api/collections/{task_id}/my-submission", headers=auth(student), data={"answers": '{"name":"张三","date":"2026-09-02","choice":"参加"}', "submit": "true"}, files={"attachment": ("form.pdf", b"%PDF-test", "application/pdf")})
        assert valid.status_code == 200 and valid.json()["attachment_name"] == "form.pdf"
        client.delete(f"/api/collections/{task_id}", headers=auth(secretary))
