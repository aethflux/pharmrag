# MedAgent RAG Agent

MedAgent 是一个面向医药问答场景的 RAG Agent Demo，支持 ModelScope/OpenAI 兼容模型、FAISS 检索、双知识库开关、单轮文件/图片提问、OCR、视觉摘要、长期记忆、FastAPI 和 Streamlit UI。

## 核心功能

- 多 Provider 接入：默认使用 `ModelScope`，聊天模型可切换 `ModelScope` 或 `OpenAI`；Embedding 可独立选择 `ModelScope`、`OpenAI` 或关闭向量检索。
- 单轮附件提问：聊天时可上传 `txt/md/json/csv/docx/pdf/png/jpg/jpeg/webp`，附件仅参与当前问题。
- 图片理解：图片先走 OCR；开启视觉模型后，会额外调用视觉模型生成图片摘要。
- 双知识库：医疗知识库和个人信息库独立管理，两个库都有开关，开启后才进入模型上下文。
- 知识导入：支持文件上传、文本粘贴、URL 导入和扫描版 PDF/图片 OCR 入库。
- FAISS RAG：使用本地 FAISS 索引，支持 `vector / hybrid / keyword` 检索和关键词兜底。
- 来源折叠：回答主体、附件解析、回答依据和参考来源分区展示，前端默认折叠依据和来源。
- 安全约束：对紧急风险、诊断判断、个体化用药调整、医疗图片提问做规则级防护。
- 历史会话：本地保存会话历史、会话列表和摘要记忆。
- API 服务：提供 `/chat`、`/knowledge/upload`、`/knowledge/url`、`/eval/retrieval` 等 FastAPI 接口。
- 评测与 CI：提供 pytest、retrieval eval、answer eval，GitHub Actions 使用离线配置运行。

## 技术栈

- Python / Streamlit / FastAPI
- LangChain / LangGraph / OpenAI SDK
- FAISS / OpenAI-compatible Embeddings
- pypdf / python-docx / BeautifulSoup4
- Pillow / pytesseract / pypdfium2
- pytest / GitHub Actions / Docker Compose

## RAG 与附件设计

- 长期知识库：医疗资料默认读取 `knowledge/`，个人资料默认读取 `personal_knowledge/`。网页导入会生成 Markdown 快照，便于复现索引。
- 单轮附件：聊天区上传的附件只进入当前 prompt，不会自动写入知识库。用户勾选“将本次提问加入个人信息库”时，只保存问题和可解析摘要。
- 文档解析：`md/txt/json/jsonl/csv/docx/pdf/html` 走文本抽取；扫描版 PDF 和图片走 OCR；图片可额外走视觉模型。
- 文本切分：先按 Markdown 标题切成证据块，再对长段落做二次切分，减少不同主题混入同一上下文。
- 混合检索：FAISS 负责语义召回，`jieba + regex token` 负责药名、剂量、禁忌词等精确命中。
- 相关性门控：进入模型上下文前会根据查询特异词、标题命中、命中词覆盖和相关性分数过滤低相关片段。
- 索引缓存：manifest 记录 embedding provider/model、知识库路径、文件 hash、OCR 配置和 loader version；配置或文件变化后自动重建。

## 系统架构

```text
User
  |
  v
Streamlit UI / FastAPI
  |
  |-- Single-turn Attachments
  |      |-- Text/PDF/DOCX extraction
  |      |-- OCR
  |      |-- Vision summary
  |
  v
MedicalAgent
  |-- risk_check
  |-- attachment_extract
  |-- retrieve
  |-- answer
  |-- citation_verify
  |-- safety_postprocess
  |-- log_metrics
  |
  |-----------------------------|
  v                             v
ModelScope / OpenAI          Memory
                              |
                              v
FAISS + Keyword Retrieval -> Medical KB / Personal KB
```

## 本地启动

本地启动适合开发调试，会使用当前机器的 Python、虚拟环境和本机 Tesseract。

### 1. 安装依赖

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置 `.env`

复制 `.env.example` 为 `.env`，至少配置 ModelScope Key：

```env
LLM_PROVIDER=modelscope
EMBEDDING_PROVIDER=modelscope
MODELSCOPE_API_KEY=your-modelscope-key

VISION_ENABLED=true
VISION_PROVIDER=modelscope
VISION_MODEL=Qwen/Qwen2.5-VL-72B-Instruct

MEDICAL_KNOWLEDGE_ENABLED=true
PERSONAL_KNOWLEDGE_ENABLED=false
RETRIEVAL_MODE=auto
```

OCR 依赖本机 Tesseract：

```env
OCR_ENABLED=true
OCR_LANG=chi_sim+eng
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### 3. 启动 Streamlit

```powershell
.\start_medagent.ps1
```

关闭服务：

```powershell
.\stop_medagent.ps1
```

也可以直接启动：

```powershell
streamlit run app.py
```

### 4. 启动 FastAPI

```powershell
uvicorn api:app --host 0.0.0.0 --port 8000
```

健康检查：

```powershell
curl http://localhost:8000/health
```

## Docker 一键部署

Docker 部署适合在新机器、演示环境或服务器上快速运行。目标机器只需要安装 Docker Desktop 或 Docker Engine，不需要手动创建 Python 虚拟环境，也不需要手动安装 Python 依赖。镜像构建时会安装项目依赖和 Tesseract OCR。

### 1. 准备环境

目标机器需要：

- Git
- Docker Desktop（Windows/macOS）或 Docker Engine + Docker Compose Plugin（Linux）
- 一个可用的 `MODELSCOPE_API_KEY`

Windows 上需要先启动 Docker Desktop，并确认 Docker Engine 已运行：

```powershell
docker version
docker compose version
```

### 2. 拉取项目

```powershell
git clone https://github.com/dayinluoyunze/medagent.git
cd medagent
```

如果是服务器，也可以通过压缩包上传项目目录，确保包含 `Dockerfile`、`docker-compose.yml`、`requirements.txt`、`app.py`、`api.py`、`agents/`、`rag/`、`knowledge/` 等文件。

### 3. 配置 `.env`

```powershell
copy .env.example .env
```

编辑 `.env`，至少填写：

```env
LLM_PROVIDER=modelscope
EMBEDDING_PROVIDER=modelscope
MODELSCOPE_API_KEY=your-modelscope-key
VISION_ENABLED=true
VISION_PROVIDER=modelscope
VISION_MODEL=Qwen/Qwen2.5-VL-72B-Instruct
```

Docker 镜像内已安装中文和英文 OCR 语言包，容器部署时通常不需要配置 `TESSERACT_CMD`。

### 4. 一键启动

```powershell
docker compose up --build
```

第一次启动会拉取 Python 基础镜像、安装系统包和 Python 依赖，耗时会比较长。构建完成后会启动两个服务：

- Streamlit 页面：`http://127.0.0.1:8501`
- FastAPI 接口：`http://127.0.0.1:8000`

后台启动：

```powershell
docker compose up -d --build
```

查看服务状态：

```powershell
docker compose ps
```

查看日志：

```powershell
docker compose logs -f
```

健康检查：

```powershell
curl http://127.0.0.1:8000/health
```

### 5. 数据保存位置

`docker-compose.yml` 会把这些本地目录挂载进容器：

- `knowledge/`：医疗知识库
- `personal_knowledge/`：个人信息库
- `.cache/vectorstore/`：FAISS 索引缓存
- `memory/`：会话历史和摘要记忆
- `logs/`：运行日志和指标

这些数据保存在宿主机项目目录中，容器重启后不会丢失。

### 6. 关闭和更新

关闭服务：

```powershell
docker compose down
```

更新代码后重新构建并启动：

```powershell
git pull
docker compose up -d --build
```

只想让容器重新读取新的 `.env`：

```powershell
docker compose up -d --force-recreate
```

完全清理容器和镜像缓存时再使用：

```powershell
docker compose down
docker image prune
```

### 7. 部署验证

```powershell
docker compose exec -T api python -m pytest -q
docker compose exec -T api python eval/run_eval.py --min-retrieval-hit-rate 0.6 --min-keyword-coverage-rate 0.4
docker compose exec -T api tesseract --list-langs
```

如果检索评测显示 `Retriever mode: vector`，说明 ModelScope Embedding 正常工作；如果显示 `keyword_fallback`，说明向量检索不可用，系统会继续使用关键词检索兜底。

## 使用流程

1. 侧边栏选择聊天模型和 Embedding 模型。
2. 输入 API Key，或让系统读取 `.env`。
3. 点击“初始化”。
4. 按需打开医疗知识库和个人信息库。
5. 在主聊天区输入问题；如需本轮附件，先上传文件或图片。
6. 如需保存某次个人背景，勾选“将本次提问加入个人信息库”后发送。
7. 回答中的附件解析、回答依据和参考来源可展开查看。

示例问题：

- 这张药盒截图里的药应该注意什么？
- 根据这份检查报告，我需要关注哪些指标？
- 二甲双胍应该饭前吃还是饭后吃？
- 这张外伤图片应该先怎么处理？

## API 示例

```bash
curl -X POST http://localhost:8000/chat \
  -F "message=根据附件说明这个药的注意事项" \
  -F "files=@drug_box.png" \
  -F "medical_knowledge_enabled=true" \
  -F "personal_knowledge_enabled=false"
```

返回字段包括：

- `answer`
- `sources`
- `attachment_reports`
- `risk_flags`
- `provider`
- `model`
- `metrics`

## 评测

检索评测：

```powershell
python eval/run_eval.py --min-retrieval-hit-rate 0.6 --min-keyword-coverage-rate 0.4
```

答案评测：

```powershell
python eval/run_answer_eval.py --provider modelscope --api-key your-modelscope-key
```

当前指标包括：

- `retrieval_hit_rate`
- `source_hit_rate`
- `keyword_coverage_rate`
- `citation_pass_rate`
- `guardrail_pass_rate`
- `attachment_grounding_rate`
- `forbidden_keyword_pass_rate`

## 测试

```powershell
python -m pytest
```

覆盖范围：

- provider 配置
- 单轮附件解析
- OCR 与视觉降级
- FastAPI multipart 上传
- 医疗/个人知识库开关
- FAISS manifest 与检索回退
- 回答依据和参考来源折叠
- 安全分级和本地 fallback

## 日志与指标

每次问答会写入 `logs/chat_metrics.jsonl`。

主要字段：

- `provider`
- `embedding_provider`
- `question_redacted`
- `attachments`
- `workflow_steps`
- `knowledge_hit`
- `knowledge_bases_hit`
- `retrieved_doc_count`
- `source_labels`
- `fallback_used`
- `status`
- `error_type`
- `risk_level`
- `risk_flags`
- `duration_ms`

## 已知限制

- 医疗图片回答只能提供一般建议和风险提示，不能替代医生诊断。
- 影像片、皮疹、外伤照片的判断需要线下医生结合病史和检查。
- 视觉模型可用性取决于当前 provider 的模型服务。
- 更换 Embedding 模型后需要重建 FAISS 索引。
