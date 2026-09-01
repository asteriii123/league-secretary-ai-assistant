# 团支书 AI 助手

这是团支书端和学生端的基础框架，并加入了第一版 DeepSeek 测试功能。
点击查看：https://league-secretary-ai-web.onrender.com/

## 当前包含

- Vue 3 + TypeScript + Vite 前端
- 班级与身份选择页（静态演示班级）
- 团支书工作台和学生工作台
- FastAPI 后端、健康检查和 DeepSeek 统一调用接口
- 学生端团务问答（暂未接本地知识库）
- 会议文字稿脱敏与结构化总结
- 基础后端测试

## 当前不包含

真实登录、数据库、通知、信息收集、文件上传、LangGraph、本地知识库、音视频转写和飞书机器人。会议总结目前需要手动粘贴已经转写好的文字稿。

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
Copy-Item .env.example .env
# 打开 .env，将 DEEPSEEK_API_KEY= 后面填写为自己的密钥
uvicorn app.main:app --reload --env-file .env
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

## 配置 DeepSeek

密钥只配置在 FastAPI 后端，不能填写在 Vue 前端，也不能提交到 GitHub。

1. 在 DeepSeek 开放平台创建 API Key。
2. 本地开发时复制 `backend/.env.example` 为 `backend/.env`，填写 `DEEPSEEK_API_KEY`。
3. `backend/.env` 已被 `.gitignore` 忽略，不会上传到 GitHub。
4. 启动后可打开 `http://127.0.0.1:8000/api/ai/status` 检查 `configured` 是否为 `true`；该接口不会显示密钥。

学生问答尚未接本地知识库，因此页面会提示回答只供测试参考。会议文字稿会在后端隐藏常见的姓名、学号、手机号和身份证号后再发给 DeepSeek，但使用者仍应避免提交敏感或涉密内容。

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

## Render 在线部署

仓库根目录的 `render.yaml` 会创建两个服务：

- `league-secretary-ai-web`：Vue 静态网站。
- `league-secretary-ai-api`：FastAPI 后端服务。

在 Render 控制台选择 **New → Blueprint**，连接本仓库并应用 Blueprint。部署完成后打开：

```text
https://league-secretary-ai-web.onrender.com
```

首次同步时，Render 会要求填写 `DEEPSEEK_API_KEY`。如果没有出现输入框，可进入 `league-secretary-ai-api` 服务的 **Environment** 页面，新增同名 Secret，然后保存并重新部署。不要把真实密钥写进 `render.yaml`。

如果 Render 提示服务名称已被占用，需要同步修改 `render.yaml` 中的服务名称、`FRONTEND_ORIGIN` 和 `VITE_API_BASE_URL`，然后重新部署。
