# 团支书 AI 助手

这是只在当前Windows电脑运行的团务协作平台。项目仅有团支书端和学生端，不设置管理员端。

第二阶段采用逐阶段开发。当前已完成本地SQLite账号基础、两端ChatGPT式流式聊天、通知管理、信息收集和会议助手。RAG将在后续阶段逐项开发。

完整方案见 [docs/团支书AI助手第二阶段本地开发方案.md](docs/团支书AI助手第二阶段本地开发方案.md)。

## 当前技术

- 前端：Vue 3、TypeScript、Vite。
- 后端：FastAPI。
- 本地数据库：SQLite、SQLAlchemy。
- 登录：本地JWT、PBKDF2密码哈希。
- AI：DeepSeek API流式多轮聊天，后续接入魔搭Embedding和Rerank。

## 第二阶段聊天功能

- 团支书端和学生端首页均有AI聊天区。
- 支持当前页面内多轮对话、逐步输出、停止生成、清空和失败重试。
- 刷新页面后聊天记录会清空，不写入SQLite。
- 当前尚未接入本地知识库，页面会明确提示回答属于通用建议。
- 聊天接口需要登录令牌，未登录请求会被拒绝。

## 第三阶段通知管理

- 团支书可创建、编辑、发布、撤回和删除本班通知。
- 通知支持截止时间、单个附件和DeepSeek辅助起草，AI草稿必须由团支书确认后发布。
- 团支书可查看本班学生的已读、未读名单。
- 学生只能查看本班已发布通知，可记录已读状态并下载附件。
- 附件最大20MB，保存在 `backend/data/uploads/notices`，不会上传GitHub。

## 第四阶段信息收集

- 团支书可创建、编辑、发布、结束和删除本班收集任务。
- 动态表单支持文本、日期和单选字段，可设置必填、截止时间、附件要求和提交后是否允许修改。
- 团支书可查看已保存、已提交、已退回及尚未填写名单，填写原因后退回，并导出CSV汇总。
- 学生可保存草稿、正式提交、按要求上传附件，并在退回后修改和重新提交。
- 学生只能操作自己的提交，团支书只能管理自己班级的数据。

## 第五阶段会议助手

- 支持粘贴文字稿，或上传音频、视频进行本地中文转写。
- 视频先通过FFmpeg提取音轨，再由faster-whisper识别；转写稿可人工修改。
- 发送DeepSeek前会隐藏明确标注的姓名、学号、手机号和身份证号。
- AI生成标题、摘要、主要内容、会议决定、负责人、截止时间和待办事项。
- 纪要必须由团支书人工编辑确认后保存到SQLite，历史纪要可以继续修改或删除。

音视频转写需要FFmpeg。Windows可以执行：

```powershell
winget install --id Gyan.FFmpeg --source winget
```

首次转写时会联网下载 `small` Whisper模型，后续识别在本机完成。

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

后端也会自动读取 `backend/.env`，因此使用下面的CMD命令同样可以启动：

```cmd
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
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

## 检查当前阶段

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

当前阶段验收包括：

- 首次启动自动建立SQLite数据库。
- 团支书可以登录。
- 学生可以使用班级邀请码注册。
- 登录状态可在刷新后保持。
- 无令牌请求被后端拒绝。
- 学生不能读取团支书专用的班级邀请码接口。
- 数据库和本地数据目录不会提交GitHub。
- 通知草稿不会显示给学生，其他班级的通知也不可见。
- 学生不能创建、编辑或删除通知。
- 通知已读状态、附件下载和AI辅助起草接口可正常使用。
- 信息收集支持动态表单、退回重交、附件校验和CSV导出。

## 后续阶段

1. Small-to-Big文档解析。
2. Chroma、BM25、RRF和Rerank。
3. RAGAS测评。

每个阶段单独验收后再开始下一阶段，不进行Render或其他线上部署。
