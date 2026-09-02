from fastapi.testclient import TestClient

from app.main import app


def login(client: TestClient, username: str, password: str = "123456") -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def student_token(client: TestClient) -> str:
    response = client.post("/api/auth/register", json={"username": "meeting-student", "password": "123456", "display_name": "会议测试学生", "invite_code": "JSJ23-1"})
    return login(client, "meeting-student") if response.status_code == 409 else response.json()["access_token"]


def payload(**changes) -> dict:
    data = {
        "meeting_type": "主题团日", "title": "九月主题团日", "transcript": "今天讨论九月主题团日活动安排，并明确了后续工作。",
        "summary": "会议明确了活动安排。", "key_points": ["讨论活动方案"], "decisions": ["本周完成准备"],
        "action_items": [{"task": "准备材料", "owner": "团支书", "deadline": "周五"}],
    }
    data.update(changes)
    return data


def test_meeting_record_persistence_permissions_and_delete() -> None:
    with TestClient(app) as client:
        secretary = login(client, "secretary1"); other = login(client, "secretary2"); student = student_token(client)
        created = client.post("/api/meetings", headers=auth(secretary), json=payload())
        assert created.status_code == 201
        record_id = created.json()["id"]
        assert any(item["id"] == record_id for item in client.get("/api/meetings", headers=auth(secretary)).json())
        assert all(item["id"] != record_id for item in client.get("/api/meetings", headers=auth(other)).json())
        assert client.get("/api/meetings", headers=auth(student)).status_code == 403
        updated = client.patch(f"/api/meetings/{record_id}", headers=auth(secretary), json=payload(summary="人工修订后的摘要。"))
        assert updated.status_code == 200 and updated.json()["summary"] == "人工修订后的摘要。"
        assert client.delete(f"/api/meetings/{record_id}", headers=auth(secretary)).status_code == 204


def test_audio_transcription_upload_and_save(monkeypatch) -> None:
    monkeypatch.setattr("app.routers.meetings.transcribe_media", lambda source: "这是本地语音识别得到的会议文字稿，内容可以由团支书继续修改。")
    with TestClient(app) as client:
        secretary = login(client, "secretary1")
        response = client.post("/api/meetings/transcribe", headers=auth(secretary), files={"file": ("meeting.mp3", b"fake-audio", "audio/mpeg")})
        assert response.status_code == 200 and response.json()["upload_id"]
        created = client.post("/api/meetings", headers=auth(secretary), json=payload(transcript=response.json()["transcript"], upload_id=response.json()["upload_id"], source_name=response.json()["source_name"]))
        assert created.status_code == 201 and created.json()["source_name"] == "meeting.mp3"
        client.delete(f"/api/meetings/{created.json()['id']}", headers=auth(secretary))


def test_invalid_media_and_student_transcription_are_rejected() -> None:
    with TestClient(app) as client:
        secretary = login(client, "secretary1"); student = student_token(client)
        invalid = client.post("/api/meetings/transcribe", headers=auth(secretary), files={"file": ("notes.txt", b"text", "text/plain")})
        assert invalid.status_code == 400
        forbidden = client.post("/api/meetings/transcribe", headers=auth(student), files={"file": ("meeting.mp3", b"audio", "audio/mpeg")})
        assert forbidden.status_code == 403
