# 后端服务

`backend` 是团支书 AI 助手的 FastAPI 后端，负责身份认证、班级业务、AI 问答、本地 RAG、联网搜索和会议 Agent。

## 目录说明

```text
backend/
├── app/
│   ├── api/routers/      # FastAPI 接口：鉴权、对话、通知、收集、知识库和会议
│   ├── core/             # 配置、数据库、权限验证和文件存储
│   ├── models/           # SQLAlchemy 数据库实体
│   ├── llm/              # DeepSeek 客户端和系统提示词
│   ├── rag/              # 文档解析、父子分块、索引、混合检索和重排
│   ├── agents/           # LangGraph 会议智能体工作流
│   ├── search/           # Tavily、百度搜索和结果合并
│   ├── services/         # Whisper 音视频转写等通用服务
│   └── main.py           # FastAPI 应用入口
├── evaluation/         # RAGAS 金标数据和评测脚本
├── tests/              # Pytest 自动化测试
├── data/               # 本地数据、附件、索引和模型（Git 忽略）
└── requirements.txt    # 后端运行依赖
```

## 启动

```powershell
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

- API：<http://127.0.0.1:8000>
- Swagger：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/api/health>

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

完整安装、配置和使用方法请查看 [项目根目录 README](../README.md)。
