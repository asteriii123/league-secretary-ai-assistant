# 团支书 AI 助手

这是只在当前Windows电脑运行的团务协作平台。项目仅有团支书端和学生端，不设置管理员端。

第二阶段采用逐阶段开发。当前已完成第一阶段：本地SQLite数据库、真实账号登录、班级权限、本地数据目录和统一配置；聊天、通知、信息收集、会议转写和RAG将在后续阶段逐项开发。

完整方案见 [docs/团支书AI助手第二阶段本地开发方案.md](docs/团支书AI助手第二阶段本地开发方案.md)。

## 当前技术

- 前端：Vue 3、TypeScript、Vite。
- 后端：FastAPI。
- 本地数据库：SQLite、SQLAlchemy。
- 登录：本地JWT、PBKDF2密码哈希。
- AI：DeepSeek API，后续接入魔搭Embedding和Rerank。

## 第一次安装

需要先安装Node.js和Python 3.11或更新版本。

### 1. 安装后端

在项目根目录打开PowerShell：

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

打开 `backend/.env`，至少修改：

```text
JWT_SECRET=换成一段仅自己知道的随机长文本
DEEPSEEK_API_KEY=你的DeepSeek密钥
```

真实密钥不能提交GitHub。`backend/.env`已加入Git忽略。

### 2. 安装前端

```powershell
cd frontend
npm install
```

## 启动项目

打开第一个PowerShell窗口：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --env-file .env
```

后端地址：

- 服务：`http://127.0.0.1:8000`
- 接口文档：`http://127.0.0.1:8000/docs`

再打开第二个PowerShell窗口：

```powershell
cd frontend
npm run dev
```

浏览器打开 `http://localhost:5173`。

## 演示账号

首次启动FastAPI时会自动初始化三个班级：

| 班级 | 团支书账号 | 初始密码 | 学生邀请码 |
|---|---|---|---|
| 23级计算机科学与技术1班 | secretary1 | 123456 | JSJ23-1 |
| 23级软件工程1班 | secretary2 | 123456 | RJGC23-1 |
| 23级数据科学与大数据技术1班 | secretary3 | 123456 | SJ23-1 |

团支书直接登录。学生在登录页选择“使用邀请码注册”。正式使用前必须修改初始密码。

## 本地数据

所有本地数据位于：

```text
backend/data/
```

其中包括SQLite数据库、后续附件和知识索引。该目录不会上传GitHub。

备份方法：

1. 关闭FastAPI。
2. 复制整个 `backend/data` 目录到安全位置。

恢复时关闭FastAPI，再用备份目录覆盖即可。

## 检查第一阶段

后端测试：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

前端检查：

```powershell
cd frontend
npm run type-check
npm run build
```

第一阶段验收包括：

- 首次启动自动建立SQLite数据库。
- 团支书可以登录。
- 学生可以使用班级邀请码注册。
- 登录状态可在刷新后保持。
- 无令牌请求被后端拒绝。
- 学生不能读取团支书专用的班级邀请码接口。
- 数据库和本地数据目录不会提交GitHub。

## 后续阶段

1. 首页ChatGPT式流式聊天。
2. 通知管理。
3. 信息收集。
4. 会议音视频转写和总结。
5. Small-to-Big文档解析。
6. Chroma、BM25、RRF和Rerank。
7. RAGAS测评。

每个阶段单独验收后再开始下一阶段，不进行Render或其他线上部署。
