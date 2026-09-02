# 团支书 AI 助手

这是只在当前Windows电脑运行的团务协作平台。项目仅有团支书端和学生端，不设置管理员端。

第二阶段采用逐阶段开发。当前已完成本地SQLite账号基础、两端ChatGPT式流式聊天、通知管理、信息收集、会议助手、知识资料解析分块和混合召回。Rerank与引用回答将在后续阶段开发。

完整方案见 [docs/团支书AI助手第二阶段本地开发方案.md](docs/团支书AI助手第二阶段本地开发方案.md)。

## 当前技术

- 前端：Vue 3、TypeScript、Vite。
- 后端：FastAPI。
- 本地数据库：SQLite、SQLAlchemy。
- 登录：本地JWT、PBKDF2密码哈希。
- AI：DeepSeek API流式多轮聊天，本地 `BAAI/bge-small-zh-v1.5` Embedding。

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

## 第六阶段知识资料

- 团支书可上传PDF、Word、PPT和TXT，单文件最大50MB。
- Word和PPT通过LibreOffice Headless转PDF；电子PDF用Docling解析（未安装Docling时自动回退PyMuPDF逐页提取）；扫描PDF用Tesseract OCR；TXT直接读取。
- 解析结果保留标题、段落、页码和章节路径，再按Small-to-Big切分为父子块。
- 父块目标800～1500字（最大2000字）保存到SQLite；小块目标200～350字、重叠约50字并记录`parent_id`，小块仅用于后续检索，不直接交给DeepSeek。
- 相同内容的文件通过SHA-256哈希去重，不会重复建立索引。
- 解析失败会保留失败原因，可重新处理；文档可停用、删除。

知识资料解析需要以下本地依赖：

```powershell
# LibreOffice用于Word、PPT转PDF
winget install --id TheDocumentFoundation.LibreOffice --source winget
# Tesseract OCR主程序（用于扫描PDF）
winget install --id UB-Mannheim.TesseractOCR --source winget
```

中文OCR语言包 `chi_sim.traineddata`（winget默认不安装中文）需放到 `backend/data/tessdata/`，可从 tessdata_fast 仓库下载。后端Python依赖（PyMuPDF、pytesseract、Pillow）通过 `pip install -r requirements.txt` 安装；Docling为可选增强，体积较大，未安装时电子PDF自动回退PyMuPDF。

## 第七阶段混合召回

- 解析完成的小块由本机 `BAAI/bge-small-zh-v1.5` 生成Embedding，资料不会发送给第三方；模型首次使用时下载到 `backend/data/models`。
- 向量保存在 `backend/data/chroma`，Jieba分词后的BM25索引保存在 `backend/data/indexes`。
- 查询时Chroma与BM25各召回top-50，以RRF `k=60`融合、去重并保留top-20。
- 所有结果按当前班级和资料启用状态过滤；停用或删除资料会同步更新两路索引。
- 知识资料页面提供调试框，可分别查看向量、BM25和RRF排名。本阶段只返回候选小块，不做Rerank或AI回答。

本地Embedding配置：

```text
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
EMBEDDING_DEVICE=cpu
LOCAL_MODEL_CACHE_DIR=./data/models
```

## 第八阶段Rerank与引用回答

- RRF融合后的top-20小块调用魔搭 `BAAI/bge-reranker-v2-m3` 重新排序，默认保留top-3。
- 系统根据小块的 `parent_id` 回溯SQLite中的父块，同一父块只发送给DeepSeek一次。
- DeepSeek回答会使用 `[资料1]` 格式引用；前端同时显示文件名、章节和页码。
- 确定性政策问题只能依据本班已启用资料。没有足够资料时必须说明“知识库依据不足”，通用建议会与资料结论分开。
- 团支书可在知识资料页面查看向量、BM25、RRF、Rerank和最终父块五段调试结果；学生不能调用调试接口。

使用前还需确认 `backend/.env` 包含：

```text
MODELSCOPE_RERANK_MODEL=BAAI/bge-reranker-v2-m3
RAG_FINAL_TOP_K=3
RAG_ENABLED=true
```

## 第九阶段RAGAS离线测评

测评不是日常启动必需功能。需要测评时，在后端虚拟环境额外安装：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements-eval.txt
```

先打开 `backend/evaluation/gold_dataset.json`。30道题的分类和问题已经建立，请根据你实际上传的正式资料填写：

```json
{
  "reference_answer": "根据正式资料人工整理的标准答案",
  "reference_contexts": ["支持标准答案的原文段落"],
  "ready": true
}
```

不要让AI自动编造标准答案。只检查模板、不调用API：

```powershell
python -m evaluation.run_ragas --validate-only
```

填写少量题后可先试跑，避免一次消耗太多API调用：

```powershell
python -m evaluation.run_ragas --class-id 1 --limit 2
```

30题全部完成后运行正式测评：

```powershell
python -m evaluation.run_ragas --class-id 1
```

系统比较四种配置：两个top-3基线、完整top-3和完整top-5。结果写入 `backend/data/evaluations`：

- JSON：完整逐题数据、汇总和自动结论。
- CSV：便于Excel检查每题结果。
- Markdown：四种方案得分、阈值、无答案检查和top-k建议。

RAGAS、DeepSeek和魔搭会产生多次API调用。模板未全部ready时，正式测评会拒绝运行；`--validate-only`不会调用任何API。

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
MODELSCOPE_API_TOKEN=你的魔搭访问令牌（当前仅预留给Rerank）
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
- 小块可写入Chroma与BM25，混合召回结果包含两路排名和RRF分数。
- Rerank默认选择top-3小块，回溯父块后流式回答并显示文件、章节和页码引用。
- RAGAS金标模板严格包含30题指定分类，未填写金标时不会运行正式测评。
- 测评可重复输出JSON、CSV和Markdown，并比较三套检索方案及top-3/top-5。

## 后续阶段

1. 根据实际知识资料人工填写30题金标并运行首份真实RAGAS报告。
2. 一键启动、备份与最终文档整理。

每个阶段单独验收后再开始下一阶段，不进行Render或其他线上部署。
