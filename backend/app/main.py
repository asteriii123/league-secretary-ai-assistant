import os
from typing import Literal

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.ai import router as ai_router


app = FastAPI(
    title="团支书 AI 助手 API",
    description="项目第一阶段的 FastAPI 基础服务。",
    version="0.1.0",
)

allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
frontend_origin = os.getenv("FRONTEND_ORIGIN", "").strip().rstrip("/")
if frontend_origin:
    allowed_origins.append(frontend_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router)


@app.get("/", tags=["基础"])
async def root() -> dict[str, str]:
    return {"message": "团支书 AI 助手后端正在运行"}


@app.get("/api/health", tags=["基础"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "league-secretary-ai-assistant"}


@app.get("/api/welcome", tags=["演示"])
async def welcome(
    role: Literal["secretary", "student"] = Query(default="student"),
) -> dict[str, str]:
    role_name = "团支书" if role == "secretary" else "学生"
    return {
        "message": f"你好，{role_name}！前端已经成功连接 FastAPI。",
        "role": role,
    }
