# 团支书 AI 助手

这是项目第一阶段的基础框架。目前只有团支书端和学生端，用于确认 Vue 前端与 FastAPI 后端可以正常启动和连接。

## 当前包含

- Vue 3 + TypeScript + Vite 前端
- 班级与身份选择页（静态演示班级）
- 团支书工作台和学生工作台
- FastAPI 后端、健康检查和演示接口
- 基础后端测试

## 当前不包含

真实登录、数据库、通知、信息收集、文件上传、LangGraph、本地知识库、音视频解析和飞书机器人。这些功能只显示入口，不在第一阶段实现。

## 目录

```text
团支书助手/
├─ frontend/              # Vue 前端
│  └─ src/
│     ├─ api/             # 后端请求
│     ├─ components/      # 公共页面布局
│     ├─ config/          # 静态演示班级
│     ├─ router/          # 页面路由
│     ├─ stores/          # 当前班级和身份
│     └─ views/           # 登录、团支书端和学生端页面
└─ backend/
   ├─ app/main.py         # FastAPI 入口
   └─ tests/              # 后端测试
```

## 第一次运行

需要先安装 Node.js 和 Python 3.11 或更新版本。

### 1. 启动后端

在项目目录打开 PowerShell：

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

后端地址是 `http://127.0.0.1:8000`，接口文档是 `http://127.0.0.1:8000/docs`。

### 2. 启动前端

再打开一个 PowerShell 窗口：

```powershell
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:5173`，先选择演示班级，再选择团支书或学生身份。

## 检查项目

前端类型检查和构建：

```powershell
cd frontend
npm run type-check
npm run build
```

后端测试（需要先激活后端虚拟环境）：

```powershell
cd backend
pytest
```

## 后续技术方向

- 前端：Vue
- 后端：FastAPI
- Agent：LangGraph
- 数据库：待确定
- RAG：本地知识库
- 多模态：音频和视频解析
- 飞书：机器人通知

数据库和各项 AI 技术会在实际开发对应功能时再确定和接入，不提前增加复杂架构。
