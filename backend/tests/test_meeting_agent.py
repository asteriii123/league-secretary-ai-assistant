import json

from fastapi.testclient import TestClient

from app.main import app


def login(client: TestClient, username: str = "secretary1") -> dict[str, str]:
    response = client.post("/api/auth/login", json={"username": username, "password": "123456"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_meeting_agent_pauses_for_two_reviews_and_builds_docx(monkeypatch) -> None:
    monkeypatch.setattr("app.meeting_agent.transcribe_media", lambda _: "这是会议的本地转写稿，内容足够长，需要先由团支书人工确认。")
    responses = iter([
        "这是脱敏并去除口头语后的会议文字稿。",
        json.dumps({"title": "测试会议", "summary": "会议摘要", "key_points": ["主要内容"], "decisions": ["会议决定"], "action_items": [{"task": "完成材料", "owner": "团支书", "deadline": "周五"}]}, ensure_ascii=False),
    ])

    async def fake_complete(self, messages, *, json_output=False):
        return next(responses)

    monkeypatch.setattr("app.meeting_agent.DeepSeekClient.complete", fake_complete)
    with TestClient(app) as client:
        auth = login(client)
        conversation = client.post("/api/ai/conversations", headers=auth).json()
        created = client.post(
            "/api/ai/meeting-jobs", headers=auth,
            data={"conversation_id": conversation["id"], "instruction": "这是主题团日，请重点整理后续待办。"},
            files={"file": ("meeting.mp3", b"fake audio", "audio/mpeg")},
        )
        assert created.status_code == 202
        assert created.json()["meeting_type"] == "主题团日"
        job_id = created.json()["id"]
        review = client.get(f"/api/ai/meeting-jobs/{job_id}", headers=auth).json()
        assert review["status"] == "awaiting_transcript_review"
        resumed = client.post(f"/api/ai/meeting-jobs/{job_id}/resume-transcript", headers=auth, json={"transcript": review["transcript"]})
        assert resumed.status_code == 202
        minutes_review = client.get(f"/api/ai/meeting-jobs/{job_id}", headers=auth).json()
        assert minutes_review["status"] == "awaiting_minutes_review"
        confirmed = client.post(f"/api/ai/meeting-jobs/{job_id}/confirm-minutes", headers=auth, json=minutes_review["minutes"])
        assert confirmed.status_code == 202
        finished = client.get(f"/api/ai/meeting-jobs/{job_id}", headers=auth).json()
        assert finished["status"] == "complete" and finished["download_ready"] is True
        document = client.get(f"/api/ai/meeting-jobs/{job_id}/document", headers=auth)
        assert document.status_code == 200 and document.content.startswith(b"PK")
