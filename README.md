# 团支书 AI 助手

团支书 AI 助手是一套只在本地 Windows 电脑运行的高校团务协作平台。系统仅包含团支书端和学生端，不设置管理员端。

团支书可以管理本班通知、信息收集、会议纪要和知识资料；学生可以查看本班通知、提交信息与附件，并通过统一AI对话查询团务知识。项目不区分“知识问答”和“会议整理”聊天模式：文字问题自动走RAG，团支书发送音视频自动进入LangGraph会议流程。

完整产品与技术方案见 [团支书AI助手第二阶段本地开发方案](docs/团支书AI助手第二阶段本地开发方案.md)。

## 当前已经实现

- 本地账号注册、登录、JWT身份验证和班级隔离。
- 统一AI对话中心，支持SQLite历史会话、多轮上下文、SSE流式输出和停止生成。
- AI回答支持Markdown标题、列表、表格、代码块和安全链接渲染。
- 普通寒暄自动跳过RAG，低相关检索结果不进入回答，也不显示错误引用。
- 角色化全局侧栏：工作台功能可折叠，AI对话保持独立入口，手机端使用抽屉导航。
- 通知创建、发布、撤回、附件下载和学生已读统计。
- 动态信息收集、附件提交、退回重交和CSV导出。
- LangGraph会议Agent：音视频转写、人工确认、脱敏去冗余、纪要确认和Word导出。
- PDF、Word、PPT和TXT知识资料解析与Small-to-Big父子分块。
- 本地Embedding、Chroma、BM25、RRF和本地Cross-Encoder Rerank。
- 父块回溯、资料引用回答和团支书专用检索调试。
- RAGAS 30题金标模板、四组方案对比和三种报告输出。

## 技术边界

| 部分 | 当前技术 |
|---|---|
| 前端 | Vue 3、TypeScript、Vite |
| 后端 | FastAPI |
| 业务数据库 | SQLite、SQLAlchemy |
| 登录 | 本地JWT、PBKDF2密码哈希 |
| 大模型 | DeepSeek API |
| Embedding | 本地 `BAAI/bge-small-zh-v1.5` |
| Rerank | 本地 `BAAI/bge-reranker-base` |
| 向量库 | 本地Chroma |
| 全文检索 | Jieba、BM25 |
| 音视频转写 | FFmpeg、faster-whisper |
| 会议流程 | LangGraph、SQLite Checkpointer |
| 文档导出 | python-docx |

业务数据、附件、知识原文、向量索引和AI模型都保存在本机。Embedding和Rerank不会把资料发送给第三方；只有最终DeepSeek回答需要联网并会接收检索到的父块内容。

## 运行环境

建议使用：

- Windows 10或Windows 11。
- Python 3.11或3.12。
- Node.js 20或更新版本。
- 至少8GB内存，建议16GB。
- 至少5GB可用磁盘空间。

Word、PPT、扫描PDF、音视频功能还需要：

```powershell
winget install --id TheDocumentFoundation.LibreOffice --source winget
winget install --id UB-Mannheim.TesseractOCR --source winget
winget install --id Gyan.FFmpeg --source winget
```

扫描版中文PDF需要 `chi_sim.traineddata`，将它放到 `backend/data/tessdata/`。

## 第一次安装

以下命令都要在PowerShell或CMD终端中执行，不能双击 `.ps1` 文件。

### 1. 安装后端

在项目根目录打开PowerShell：

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

如果PowerShell禁止运行激活脚本，可以不激活，直接使用：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. 配置后端

打开 `backend/.env`，至少修改：

```text
JWT_SECRET=换成一段仅自己知道的随机长文本
DEEPSEEK_API_KEY=你的DeepSeek密钥
```

本地RAG推荐保持以下配置：

```text
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
EMBEDDING_DEVICE=cpu
LOCAL_MODEL_CACHE_DIR=./data/models
EMBEDDING_BATCH_SIZE=16

RERANK_PROVIDER=local
RERANK_MODEL=BAAI/bge-reranker-base
RERANK_DEVICE=cpu
RERANK_BATCH_SIZE=4

RAG_ENABLED=true
RAG_FINAL_TOP_K=3
RAG_RECALL_TOP_K=50
RAG_RRF_K=60
RAG_FUSION_TOP_K=20
RAG_MIN_RERANK_SCORE=0.35
```

真实密钥只能放在 `backend/.env`，不能写入README或提交到GitHub。当前本地RAG不需要魔搭Token，`.env.example`中的魔搭配置只是兼容旧配置的预留项。

### 3. 安装前端

回到项目根目录，再执行：

```powershell
cd frontend
npm install
```

## 启动项目

需要同时启动后端和前端。

### 1. 启动后端

打开第一个PowerShell窗口：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

不激活虚拟环境也可以启动：

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

后端地址：

- API服务：`http://127.0.0.1:8000`
- 健康检查：`http://127.0.0.1:8000/api/health`
- 接口文档：`http://127.0.0.1:8000/docs`

### 2. 启动前端

打开第二个PowerShell窗口：

```powershell
cd frontend
npm run dev
```

浏览器打开 `http://localhost:5173`。

修改 `.env`、Embedding模型或Rerank模型后，必须重新启动FastAPI。

## 演示账号

首次启动FastAPI会自动初始化三个班级：

| 班级 | 团支书账号 | 初始密码 | 学生邀请码 |
|---|---|---|---|
| 23级计算机科学与技术1班 | `secretary1` | `123456` | `JSJ23-1` |
| 23级软件工程1班 | `secretary2` | `123456` | `RJGC23-1` |
| 23级数据科学与大数据技术1班 | `secretary3` | `123456` | `SJ23-1` |

团支书直接登录。学生在登录页选择“使用邀请码注册”。正式使用前应修改演示密码和 `JWT_SECRET`。

## 使用本地知识库

### 1. 上传资料

使用团支书账号登录，在团支书工作台进入“知识资料”，上传：

- PDF。
- Word：`.doc`、`.docx`。
- PPT：`.ppt`、`.pptx`。
- TXT。

单文件最大50MB。建议上传学校或学院正式发布的团费、入团入党、团员评议、主题团日和组织关系转接材料。

### 2. 等待处理完成

资料依次经过：

```text
文件解析
→ Small-to-Big父子分块
→ 本地Embedding
→ 写入Chroma和BM25
→ 索引完成
```

页面出现“完成”和“索引完成”后，资料才能用于聊天。失败时页面会显示原因，可以点击“重新索引”。

模型首次使用时需要联网下载到 `backend/data/models`。Embedding模型较小；Rerank模型约1GB，首次下载和首次CPU加载会比较慢，后续直接使用本地缓存。

### 3. 测试完整检索链路

知识资料页面的“RAG完整检索链路”可以查看：

```text
Chroma向量top-50
＋ BM25全文top-50
→ RRF融合top-20
→ 本地Rerank top-3
→ 回溯并去重父块
```

该调试功能只有团支书可以使用，学生不能查看检索中间结果。

### 4. 在 AI 对话中心提问

登录后点击绿色全局侧栏中的“AI 对话”。左侧可新建、切换和删除历史会话；历史会话保存在SQLite，刷新、退出或重启后仍然存在。例如：

```text
根据本班知识库，入党积极分子需要接受哪些培养和考察？
```

回答会显示类似引用：

```text
[资料1] 文件名 · 章节 · 第2页
```

确定性政策问题只能依据本班已启用资料回答。资料不足时，系统应明确说明“知识库依据不足”，不能虚构政策、日期或引用。

系统会跳过“你好、谢谢”等日常寒暄的知识库检索，并通过本地Rerank相关性门槛过滤无关结果。只有实际采用了本班资料的回答才显示引用；门槛可在 `backend/.env` 中通过 `RAG_MIN_RERANK_SCORE` 调整，默认值为 `0.35`。

团支书端不需要选择“知识问答”或“会议整理”：直接发送文字时，系统自动检索本班RAG知识库并流式回答；添加一个音频或视频时，系统自动启动LangGraph会议Agent。可以同时填写“这是本周团课录音，请重点整理后续待办”等要求，也可以不填文字直接发送。学生端只显示文字提问，不显示音视频附件按钮。

绿色侧栏中的“班级工作台/我的工作台”可以展开或收起。团支书可从小导航进入通知管理、信息收集、知识资料和会议文档；学生可进入本班通知和信息收集。“AI 对话”始终作为独立入口显示，首页不再重复放置AI功能卡。

## RAG工作原理

构建知识库：

```text
Word/PPT转PDF
→ PDF/TXT解析
→ 父块800～1500字
→ 小块200～350字、约50字重叠
→ 本地Embedding
→ Chroma和BM25
```

用户提问：

```text
寒暄判断（你好、谢谢等直接跳过RAG）
→ 问题本地Embedding
→ Chroma和BM25各召回top-50
→ RRF融合top-20
→ 本地Cross-Encoder Rerank
→ 过滤低于相关性门槛的结果
→ top-3小块回溯父块
→ DeepSeek根据父块流式回答并显示引用
```

小块只用于精确检索，最终传给DeepSeek的是信息更完整的父块。同一父块被多个小块命中时只发送一次。只有通过相关性门槛并实际交给DeepSeek的资料才会显示在回答下方；普通聊天和无关问题不会强行附带资料来源。

## 其他业务功能

### 通知管理

- 团支书创建、编辑、发布、撤回和删除本班通知。
- 支持截止时间、附件和DeepSeek辅助起草。
- 学生只能看到本班已发布通知，可以记录已读并下载附件。
- 团支书可以查看已读和未读学生名单。

### 信息收集

- 团支书创建文本、日期和单选动态字段。
- 可以设置截止时间、附件要求和提交后是否允许修改。
- 学生保存草稿、正式提交、修改和退回后重新提交。
- 团支书查看提交状态、退回原因和导出CSV汇总。

### 会议助手

- 会议处理已合并到团支书的 AI 对话中心，学生无权使用。
- 在任意对话中添加最大500MB的单个音频或视频，系统自动启动会议Agent，不需要切换模式。
- 可以同时输入“这是本周团课，请重点整理后续待办”等要求；未输入时默认生成标准会议纪要。
- FFmpeg从视频提取音轨，faster-whisper在本地完成中文转写。
- LangGraph在转写后暂停，等待人工修改；然后执行脱敏、去冗余和结构化纪要。
- 明确标注的姓名、学号、手机号和身份证号会在发送DeepSeek前隐藏。
- AI纪要需再次人工确认，然后保存并生成可下载的DOCX。
- 确认后的纪要写入当前对话，可继续追问“有哪些待办”“谁负责准备材料”。
- 旧纪要和新纪要统一在“会议文档”中查看和下载。

## RAGAS离线测评

RAGAS不是日常运行必需功能。需要测评时额外安装：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements-eval.txt
```

打开 `backend/evaluation/gold_dataset.json`，根据实际正式资料人工填写：

```json
{
  "reference_answer": "人工整理的标准答案",
  "reference_contexts": ["支持标准答案的原文段落"],
  "ready": true
}
```

30题包含10道事实题、8道流程或材料题、5道跨段落题、4道相似政策辨析题和3道知识库无答案题。

只检查模板，不调用API：

```powershell
python -m evaluation.run_ragas --validate-only
```

少量试跑：

```powershell
python -m evaluation.run_ragas --class-id 1 --limit 2
```

30题正式测评：

```powershell
python -m evaluation.run_ragas --class-id 1
```

报告保存在 `backend/data/evaluations`，包含JSON、UTF-8 CSV和Markdown。测评会调用DeepSeek多次，可能产生API费用；Embedding使用本地模型。标准答案必须人工填写，程序不会使用空金标生成虚假分数。

## 本地数据与备份

所有运行数据都位于：

```text
backend/data/
├─ app.db                 # SQLite业务数据库
├─ uploads/               # 通知、提交、会议和知识原文件
├─ converted/             # Office转换结果
├─ chroma/                # 向量索引
├─ indexes/               # BM25索引
├─ models/                # Embedding和Rerank模型
├─ tessdata/              # OCR语言包
└─ evaluations/           # RAGAS报告
```

该目录已被Git忽略，不会上传GitHub。

备份：关闭FastAPI后，复制整个 `backend/data` 到安全位置。恢复时关闭FastAPI，用备份目录覆盖当前目录，再重新启动后端。

退出登录、关闭浏览器、重启前后端或重启电脑都不会删除资料。只有手动删除资料、删除 `backend/data` 或修改数据目录位置才会导致原数据不可见。

## 测试项目

后端测试：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

前端类型检查和生产构建：

```powershell
cd frontend
npm run type-check
npm run build
```

## 常见问题

### `Activate.ps1`被记事本打开

不要双击文件。请在PowerShell中进入 `backend` 后输入：

```powershell
.\.venv\Scripts\Activate.ps1
```

也可以不激活，直接使用 `.\.venv\Scripts\python.exe` 运行Python命令。

### 页面提示无法连接后端

确认FastAPI窗口仍在运行，并打开 `http://127.0.0.1:8000/api/health`，应该看到 `status: ok`。

### DeepSeek提示API Key未配置

检查 `backend/.env` 中的 `DEEPSEEK_API_KEY`，修改后重启后端。不要在前端代码中填写密钥。

### Word或PPT解析失败

确认已经安装LibreOffice，并重启后端。电子PDF在没有Docling时会回退PyMuPDF；扫描PDF还需要Tesseract和中文语言包。

### 资料解析完成但索引失败

确认已经安装完整后端依赖：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

首次模型下载必须联网。下载完成后重启后端，再点击“重新索引”。本地Embedding和Rerank不会触发魔搭的团务内容审核。

### 第一次检索很慢

这是CPU首次加载Embedding或约1GB的Rerank模型。模型进入内存后，同一次后端运行期间的后续查询会更快。

### Rerank模型下载卡住

当前电脑已经将模型保存在 `backend/data/models`。换电脑时可以备份并复制整个 `backend/data/models`，避免重新下载。

### 换Embedding模型后提示向量维度不一致

系统会根据Embedding提供方式和模型名自动使用不同Chroma集合。重新索引资料即可，不要手动修改向量数据。

## 当前待完成事项

- 根据实际知识资料人工填写30题金标并运行首份真实RAGAS报告。
- 增加Windows一键启动脚本。
- 完善本地备份和恢复工具。

项目不使用Render、Supabase或云数据库，也不包含管理员端。
