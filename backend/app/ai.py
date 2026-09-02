import json
import os
import re
from typing import Any, Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError
from app.auth import get_current_user
from app.config import settings
from app.models import User


router = APIRouter(prefix="/api/ai", tags=["AI"])

QA_DISCLAIMER = "当前版本尚未接入本地知识库，回答仅供测试参考，请以学校和学院正式文件为准。"


class StudentQuestionRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)


class StudentAnswerResponse(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list)
    has_reliable_source: bool = False
    disclaimer: str = QA_DISCLAIMER


class MeetingSummaryRequest(BaseModel):
    meeting_type: Literal["主题团日", "团课", "支部会议", "其他"]
    transcript: str = Field(min_length=20, max_length=50000)


class ActionItem(BaseModel):
    task: str
    owner: str = "未指定"
    deadline: str = "未指定"


class MeetingSummaryResponse(BaseModel):
    title: str
    meeting_type: str
    summary: str
    key_points: list[str]
    decisions: list[str]
    action_items: list[ActionItem]
    requires_manual_review: bool = True
    redacted_sensitive_data: bool


class DeepSeekError(Exception):
    pass


class DeepSeekClient:
    def __init__(self) -> None:
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url
        self.model = settings.deepseek_model

    async def complete(self, messages: list[dict[str, str]], *, json_output: bool = False) -> str:
        if not self.api_key:
            raise DeepSeekError("DEEPSEEK_API_KEY 尚未配置")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 2000,
            "stream": False,
        }
        if json_output:
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0)) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise DeepSeekError("DeepSeek 暂时无法完成请求，请稍后重试") from exc

        if not isinstance(content, str) or not content.strip():
            raise DeepSeekError("DeepSeek 返回了空内容，请稍后重试")
        return content.strip()

    async def stream(self, messages: list[dict[str, str]]):
        if not self.api_key:
            raise DeepSeekError("DEEPSEEK_API_KEY 尚未配置")
        payload = {"model": self.model, "messages": messages, "temperature": 0.2, "max_tokens": 2000, "stream": True}
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
                async with client.stream("POST", f"{self.base_url}/chat/completions", headers={"Authorization": f"Bearer {self.api_key}"}, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            content = json.loads(data)["choices"][0]["delta"].get("content", "")
                        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                            continue
                        if content:
                            yield content
        except httpx.HTTPError as exc:
            raise DeepSeekError("DeepSeek 暂时无法完成请求，请检查密钥和网络") from exc

def get_deepseek_client() -> DeepSeekClient:
    return DeepSeekClient()


def redact_sensitive_text(text: str) -> tuple[str, bool]:
    patterns = [
        (r"(?<!\d)1[3-9]\d{9}(?!\d)", "[手机号已隐藏]"),
        (r"(?<!\d)\d{17}[\dXx](?!\d)", "[身份证号已隐藏]"),
        (r"(学号[：:\s]*)([A-Za-z0-9_-]{6,20})", r"\1[已隐藏]"),
        (r"(姓名[：:\s]*)([\u4e00-\u9fff]{2,4})", r"\1[已隐藏]"),
    ]
    redacted = text
    for pattern, replacement in patterns:
        redacted = re.sub(pattern, replacement, redacted)
    return redacted, redacted != text


def ai_http_error(exc: DeepSeekError) -> HTTPException:
    status_code = 503 if "API_KEY" in str(exc) else 502
    return HTTPException(status_code=status_code, detail=str(exc))


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)


def sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    client: DeepSeekClient = Depends(get_deepseek_client),
) -> StreamingResponse:
    async def generate():
        role_prompt = (
            "协助团支书起草通知、整理工作计划、准备会议和解答团务常见问题。"
            if user.role == "secretary"
            else "帮助学生理解入团入党材料、团员义务和团务常见问题。"
        )
        system_prompt = (
            f"你是高校团务AI助手，{role_prompt}"
            "当前尚未接入本地知识库，不得虚构学校政策、文件名称、截止日期或引用来源；"
            "涉及学校具体规定时，明确建议以学校正式文件或团支书通知为准。回答使用简洁、友善的中文。"
        )
        messages = [{"role": "system", "content": system_prompt}] + [item.model_dump() for item in request.history[-10:]] + [{"role": "user", "content": request.question.strip()}]
        yield sse("status", {"stage": "generating", "message": "DeepSeek正在生成回答"})
        try:
            async for content in client.stream(messages):
                yield sse("content", {"text": content})
            yield sse("done", {"ok": True})
        except DeepSeekError as exc:
            yield sse("error", {"message": str(exc)})

    return StreamingResponse(generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/status")
async def ai_status() -> dict[str, str | bool]:
    return {
        "configured": bool(os.getenv("DEEPSEEK_API_KEY", "").strip()),
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
    }


@router.post("/student-qa", response_model=StudentAnswerResponse)
async def student_qa(
    request: StudentQuestionRequest,
    client: DeepSeekClient = Depends(get_deepseek_client),
) -> StudentAnswerResponse:
    messages = [
        {
            "role": "system",
            "content": (
                "你是高校团务问答助手。请用简洁、友善的中文回答。当前没有接入学校本地知识库，"
                "不得捏造政策、文件名称、截止日期或引用来源；遇到校级差异时，明确建议咨询本班团支书或学院老师。"
            ),
        },
        {"role": "user", "content": request.question.strip()},
    ]
    try:
        answer = await client.complete(messages)
    except DeepSeekError as exc:
        raise ai_http_error(exc) from exc
    return StudentAnswerResponse(answer=answer)


@router.post("/meeting-summary", response_model=MeetingSummaryResponse)
async def meeting_summary(
    request: MeetingSummaryRequest,
    client: DeepSeekClient = Depends(get_deepseek_client),
) -> MeetingSummaryResponse:
    transcript, was_redacted = redact_sensitive_text(request.transcript.strip())
    messages = [
        {
            "role": "system",
            "content": (
                "你是高校团务会议纪要助手。只根据提供的文字稿整理，不得补写未出现的事实。"
                "返回一个 JSON 对象，字段必须为 title、summary、key_points、decisions、action_items。"
                "key_points 和 decisions 是字符串数组；action_items 是对象数组，每项含 task、owner、deadline。"
                "未明确负责人或截止日期时填写‘未指定’。"
            ),
        },
        {"role": "user", "content": f"会议类型：{request.meeting_type}\n\n文字稿：\n{transcript}"},
    ]
    try:
        raw_result = await client.complete(messages, json_output=True)
        data = json.loads(raw_result)
        data.update(
            meeting_type=request.meeting_type,
            requires_manual_review=True,
            redacted_sensitive_data=was_redacted,
        )
        return MeetingSummaryResponse.model_validate(data)
    except DeepSeekError as exc:
        raise ai_http_error(exc) from exc
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="AI 返回格式不完整，请重新生成") from exc
