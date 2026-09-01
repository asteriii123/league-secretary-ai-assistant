import json

from fastapi.testclient import TestClient

from app.ai import get_deepseek_client, redact_sensitive_text
from app.main import app


client = TestClient(app)


class FakeDeepSeekClient:
    async def complete(self, messages: list[dict[str, str]], *, json_output: bool = False) -> str:
        if json_output:
            return json.dumps(
                {
                    "title": "九月主题团日",
                    "summary": "会议讨论了本月团务安排。",
                    "key_points": ["完成材料收集"],
                    "decisions": ["周五前完成"],
                    "action_items": [{"task": "收集材料", "owner": "团支书", "deadline": "周五"}],
                },
                ensure_ascii=False,
            )
        return "请先查看学院发布的正式通知，并咨询本班团支书。"


def setup_function() -> None:
    app.dependency_overrides[get_deepseek_client] = lambda: FakeDeepSeekClient()


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_student_qa_is_marked_as_unverified() -> None:
    response = client.post("/api/ai/student-qa", json={"question": "入党申请书应该怎么写？"})
    assert response.status_code == 200
    assert response.json()["has_reliable_source"] is False
    assert response.json()["sources"] == []
    assert "正式文件" in response.json()["disclaimer"]


def test_meeting_summary_returns_structured_result() -> None:
    response = client.post(
        "/api/ai/meeting-summary",
        json={"meeting_type": "主题团日", "transcript": "今天讨论九月主题团日，决定周五前由团支书完成材料收集。"},
    )
    assert response.status_code == 200
    assert response.json()["action_items"][0]["owner"] == "团支书"
    assert response.json()["requires_manual_review"] is True


def test_sensitive_text_is_redacted() -> None:
    text = "姓名：张三，学号：2023123456，手机13800138000，身份证110101200001011234"
    redacted, changed = redact_sensitive_text(text)
    assert changed is True
    assert "张三" not in redacted
    assert "2023123456" not in redacted
    assert "13800138000" not in redacted
    assert "110101200001011234" not in redacted


def test_rejects_short_transcript() -> None:
    response = client.post("/api/ai/meeting-summary", json={"meeting_type": "团课", "transcript": "内容太短"})
    assert response.status_code == 422
