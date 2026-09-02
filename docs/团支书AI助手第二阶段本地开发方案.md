# 团支书 AI 助手第二阶段本地开发方案

## 1. 项目目标与边界

第二阶段只在当前 Windows 电脑运行，不使用 Render、Supabase或其他云数据库。系统仅包含团支书端和学生端，不开发管理员端。

- Vue前端运行在 `http://localhost:5173`。
- FastAPI后端运行在 `http://127.0.0.1:8000`。
- SQLite保存账号、班级和业务数据。
- 本地目录保存附件、会议文件和知识资料。
- Chroma保存知识小块向量，BM25提供全文检索。
- DeepSeek API用于聊天和会议总结。
- 魔搭API用于Embedding和Rerank。
- faster-whisper用于本地音视频转写。

DeepSeek和魔搭仍需联网，其Token只保存在本地 `.env`，不得提交GitHub。

## 2. 本地账号和数据目录

业务数据库为 `backend/data/app.db`。密码使用PBKDF2-SHA256加盐哈希，登录后由FastAPI签发本地JWT。后端根据JWT中的用户查询角色和班级，不能信任前端自行声明的身份。

```text
backend/data/
├─ app.db
├─ uploads/
│  ├─ notices/
│  ├─ submissions/
│  ├─ meetings/
│  └─ knowledge/
├─ converted/
├─ chroma/
└─ indexes/
```

整个 `backend/data` 目录被Git忽略。备份时关闭后端并复制该目录即可。

初始化包含3个演示班级，团支书账号为 `secretary1`、`secretary2`、`secretary3`，初始密码均为 `123456`。学生通过对应班级邀请码注册。正式使用前必须修改演示密码和 `JWT_SECRET`。

## 3. 页面与业务模块

### ChatGPT式聊天

团支书和学生首页均设置聊天区，支持多轮上下文、SSE流式输出、停止、清空、错误重试和引用资料。聊天记录只保留在当前页面，刷新后清空。

### 通知管理

团支书创建、编辑、发布、撤回或删除本班通知，可设置截止时间、上传单个附件、调用DeepSeek生成待确认草稿，并查看本班学生的已读和未读名单。学生只能查看本班已发布通知，可下载附件并记录已读。附件最大20MB，允许PDF、Word、Excel和常见图片，同时校验扩展名、MIME和文件大小。通知、阅读记录保存SQLite，附件保存 `backend/data/uploads/notices`；删除通知时同步清理附件。已有本地数据库通过保留数据的SQLite字段迁移升级。

### 信息收集

团支书创建、编辑、发布、结束或删除收集任务，动态字段支持文本、日期和单选，可配置必填、截止时间、是否要求附件和提交后是否允许修改。团支书查看学生草稿、已提交、已退回及尚未填写名单，可填写原因退回，并导出带UTF-8 BOM的CSV汇总。学生可保存草稿、正式提交、修改允许更新的提交及在退回后重新提交。提交与答案保存在SQLite，附件保存在 `backend/data/uploads/submissions`。单文件限制20MB，支持PDF、Word、Excel和常见图片，并同时校验扩展名、MIME和大小。所有任务和提交均按角色、班级及学生本人隔离。

### 会议助手

支持粘贴文字稿，或上传最大500MB的常见音频、视频。视频由FFmpeg提取16kHz单声道音轨，faster-whisper使用中文、VAD和CPU `int8`模式完成本地转写；默认模型为 `small`，可通过环境变量调整。转写稿允许人工修改，明确标注的姓名、学号、手机号和身份证号会在发送DeepSeek前隐藏。DeepSeek只根据文字稿生成标题、摘要、主要内容、会议决定及包含负责人和截止时间的待办事项，不得补写事实。所有结果都可人工编辑，团支书确认后才保存SQLite。历史纪要可再次编辑或删除，关联的本地原始音视频随纪要删除。

### 知识资料

团支书上传PDF、Word、PPT和TXT，查看解析和索引状态，启用、停用、删除或重新索引；学生仅通过聊天使用本班已启用资料。

## 4. Small-to-Big RAG链路

```text
Office转PDF → Docling/OCR解析 → 父子分块 → BGE-M3 Embedding
→ Chroma向量top-50 + BM25全文top-50 → RRF融合top-20
→ BGE Rerank → top-3小块回溯父块 → DeepSeek引用回答
```

文档加载：LibreOffice Headless将Word、PPT转PDF；Docling输出结构化Markdown；扫描PDF使用Tesseract OCR；TXT直接读取。

分块规则：

- 父块按标题和自然段生成，目标800～1500字，最大2000字，保存SQLite。
- 小块目标200～350字，重叠约50字，记录 `parent_id`，向量保存Chroma。
- 小块只用于召回，最终传给DeepSeek的是父块。
- 保留班级、文件名、章节、页码、内容哈希和索引版本。

检索规则：Chroma和BM25分别召回top-50，以RRF `k=60`融合为top-20，再通过 `BAAI/bge-reranker-v2-m3` 重排，默认选择top-3并回溯父块。无可靠资料时必须提示“知识库依据不足”，不得伪造引用。

## 5. RAGAS测评

制作30道人工中文金标题：10道事实题、8道流程题、5道跨段落题、4道相似政策辨析题、3道无答案题。

对比：

1. 仅向量检索、小块回答。
2. Small-to-Big、仅向量召回。
3. Small-to-Big、混合召回和Rerank。

指标为Faithfulness、Answer Relevance、Context Precision和Context Recall。初始目标依次为0.85、0.80、0.75、0.75；无答案问题不得伪造引用。对比top-3和top-5后再决定是否调整默认值。

## 6. 分阶段实施状态

| 阶段 | 内容 | 状态 |
|---|---|---|
| 1 | SQLite、账号、JWT、班级权限、本地目录和配置 | 已完成 |
| 2 | 两端ChatGPT式流式聊天 | 已完成 |
| 3 | 通知管理 | 已完成 |
| 4 | 信息收集 | 已完成 |
| 5 | 会议文字稿与音视频转写 | 已完成 |
| 6 | 文档解析与Small-to-Big | 已完成 |
| 7 | Chroma、BM25和RRF | 未开始 |
| 8 | Rerank、父块回溯和引用回答 | 未开始 |
| 9 | RAGAS评测 | 未开始 |
| 10 | 一键启动、备份和最终文档 | 未开始 |

每个阶段完成后单独测试和提交Git，用户验收后再开始下一阶段，不执行任何线上部署。

## 7. 本地验收方式

每阶段至少执行后端测试、前端类型检查和前端生产构建。第五阶段需验证会议接口仅团支书可用、文字稿会脱敏、音视频类型与大小校验有效、转写稿和AI结果可人工编辑、未经确认不会保存、不同班级的纪要相互隔离，并核对FFmpeg与faster-whisper本地依赖。
