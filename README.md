# MedAgent RAG Agent

一个面向医药问答场景的 RAG Agent Demo，支持多模型切换、知识库检索、长期记忆摘要、资料上传管理、OCR 兜底和本地回退检索。

## 项目定位

这个项目聚焦医药知识问答场景，用于验证以下能力：

- 多个 OpenAI 兼容模型接口的统一接入
- 基于本地知识库的 RAG 检索增强
- 会话历史与摘要记忆管理
- 故障回退与基本安全约束

当前实现也适合作为后续扩展评测、引用溯源和安全策略的基础版本。

## 核心功能

- 多模型 Provider 切换：聊天模型支持 `OpenAI`、`ModelScope`、`MiniMax`，Embedding 模型支持独立选择 `OpenAI`、`ModelScope` 或关闭向量检索
- 多源知识库接入：支持 `md`、`txt`、`json`、`csv`、`docx`、`pdf`、图片、`html`、网页 URL
- 网页资料导入：在 UI 中粘贴 URL 后抓取正文或 PDF 文本，生成本地 Markdown 知识快照
- 知识库管理：支持查看知识文件、预览文本资料、删除网页添加资料、手动重建索引
- 单次个人资料沉淀：用户可在发送某条消息前勾选“将本次提问加入个人信息库”，仅保存该条消息
- OCR 兜底：扫描版 PDF 和图片资料可通过 Tesseract OCR 抽取文本后入库
- 检索模式：支持 `vector / hybrid / keyword`
- RAG 检索：优先使用 `FAISS + Embeddings`，Embedding Provider 可与聊天模型解耦
- 回退检索：Embedding 调用失败或查询期异常时自动退回本地关键词检索
- 来源展示：回答尾部自动附带命中的知识来源和片段
- 安全分级：对紧急风险、诊断判断、个体化用药调整做规则级防护
- 长期记忆：对历史对话进行 markdown 摘要并持久化
- 故障兜底：模型调用失败时回退到本地知识库内容摘要
- Web UI：基于 Streamlit 提供交互式问答界面
- CI 验证：GitHub Actions 自动运行单元测试和离线检索评测

## 技术栈

- Python
- Streamlit
- LangChain
- OpenAI SDK
- FAISS
- python-docx
- pypdf
- pypdfium2
- pytesseract
- Pillow
- BeautifulSoup4

## 项目形态

这个项目是一个面向医药问答的轻量级 RAG Agent。

- 交互入口：用户通过聊天框提问，系统返回自然语言答案。
- Agent 编排：`MedicalAgent` 负责模型选择、RAG 检索、长期记忆、安全分级、故障回退、来源引用和指标日志。
- 工程边界：当前实现采用单 Agent 编排，围绕检索增强问答、知识库管理和安全约束展开。

## RAG 技术选型

- 知识导入：采用本地文件 + UI 上传 + URL 快照导入。URL 在用户显式添加时转成 Markdown 快照，保证索引可复现，也降低运行时网络波动对问答的影响。
- 文档解析：内置 `md/txt/json/jsonl/csv/docx/pdf/image/html` 解析。HTML 与 URL 页面会先做正文提取，PDF 会抽取页文本并保留页码标记；扫描版 PDF 或图片会走 OCR 兜底。
- 文本切分：先按 Markdown 标题切成独立证据块，再用 `RecursiveCharacterTextSplitter` 做长段落二次切分，避免同一文件中相邻主题被混入同一个上下文块。
- 向量检索：使用 `FAISS + OpenAI-compatible Embeddings`，Embedding Provider 可在 UI 中独立选择 OpenAI、ModelScope 或关闭，向量索引本地持久化。
- 混合检索：支持 `vector / hybrid / keyword`。向量检索负责语义召回，`jieba + 正则 token` 的关键词检索负责药名、剂量、禁忌词等精确命中，并在 Embedding 调用失败时兜底。
- 本地重排：`hybrid` 模式会扩大候选集，再用向量排名、查询关键词覆盖、标题/别名命中和通用医学问法同义词做 lightweight rerank，避免单纯拼接结果导致高精确命中的片段排在后面。
- 相关性门控：检索结果进入模型上下文前，会基于查询特异词、标题命中、命中词覆盖和相关性分数过滤低相关片段；知识库可通过文件、文本和 URL 持续扩充。
- 上下文呈现：每个证据块都会带来源、相关性分数和命中词，prompt 要求模型忽略明显无关片段；前端会把“回答依据”和“参考来源”折叠，默认只展示主体回答。
- 索引缓存：基于知识文件内容、Embedding 模型、检索配置生成 manifest；知识库变化后自动重建 FAISS，否则复用本地缓存。

## 系统架构

```text
User
  |
  v
Streamlit UI
  |
  |-- Upload / URL Snapshot / Knowledge Manager
  |
  v
MedicalAgent
  |------------------------------|
  |                              |
  v                              v
LLM Provider Adapter         Memory Manager
  |                              |
  v                              v
OpenAI / ModelScope /       Markdown History +
MiniMax                     Summary Persistence
  |
  v
Retriever
  |------------------------------|
  |                              |
  v                              v
FAISS Vector Search         Keyword Fallback
  |
  v
Local Knowledge Base
```

## 目录结构

```text
medagent/
├─ app.py
├─ config.py
├─ requirements.txt
├─ agents/
│  └─ medical_agent.py
├─ rag/
│  └─ retriever.py
├─ knowledge/
│  ├─ drugs.md
│  ├─ products.md
│  ├─ qa.md
│  ├─ sample.docx
│  ├─ sample.url
│  └─ sample.urls
├─ personal_knowledge/      # 本地个人资料库
└─ memory/
   ├─ conversation_history.md
   └─ conversation_summary.md
```

## 本地启动

### 1. 创建环境并安装依赖

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，并至少配置一个可用 Provider 的 API Key。

示例：

```env
LLM_PROVIDER=modelscope
EMBEDDING_PROVIDER=modelscope
MODELSCOPE_API_KEY=your-modelscope-key
ALLOW_URL_KNOWLEDGE_INGESTION=true
MEDICAL_KNOWLEDGE_ENABLED=true
PERSONAL_KNOWLEDGE_ENABLED=false
RETRIEVAL_CANDIDATE_MULTIPLIER=5
RETRIEVAL_MIN_RELEVANCE_SCORE=2.0
RETRIEVAL_MIN_SIGNAL_OVERLAP=1
```

### 3. 启动应用

```bash
streamlit run app.py
```

默认会在浏览器中打开本地页面。

如果你在 Windows 下希望一键启动，也可以直接运行项目根目录下的脚本：

```powershell
.\start_medagent.ps1
```

脚本会自动：

- 检查 `venv` 和 `.env`
- 自动寻找 `8501-8510` 范围内的可用端口
- 在后台启动 Streamlit
- 将日志写入 `logs/streamlit.out.log` 和 `logs/streamlit.err.log`
- 记录 PID 到 `logs/streamlit.pid`
- 记录实际端口到 `logs/streamlit.port`
- 自动打开浏览器

关闭服务：

```powershell
.\stop_medagent.ps1
```

如果你是直接在当前终端执行 `streamlit run app.py`，也可以用 `Ctrl + C` 结束服务。

## 使用流程

1. 在侧边栏选择聊天模型 Provider
2. 选择 Embedding Provider；它负责知识库向量化和召回，可独立于聊天模型配置
3. 输入对应 API Key，或从 `.env` 自动读取；Embedding Key 留空时会优先复用同 Provider 的聊天 Key
4. 点击“初始化 Agent”
5. 按需打开“启用医疗知识库”和“启用个人信息库”开关；开启的知识库会进入模型上下文
6. 如需补充知识库，在侧边栏“知识库”中选择保存目标，上传文件、粘贴文本或输入 URL 后点击“保存并刷新知识库”
7. 如果某次提问包含希望长期保留的个人背景，可先勾选“将本次提问加入个人信息库”，该选项只作用于下一条消息
8. 在主界面输入医药相关问题

医疗资料默认读取 `knowledge/`，网页添加的医疗资料会保存到 `knowledge/uploads/`。
个人资料默认读取 `personal_knowledge/`，个人信息库默认关闭。
URL 导入会拒绝本机、内网和非 `http(s)` 地址；如需限制可导入域名，可配置 `REMOTE_KNOWLEDGE_ALLOWLIST`。
OCR 依赖本机 Tesseract 程序；如果 Windows 没有安装，可先安装 Tesseract，并在 `.env` 中配置 `TESSERACT_CMD`。
侧边栏“查看当前状态”会显示 OCR 是否可用；侧边栏“知识库”可以预览资料、删除网页添加资料并手动重建索引。

建议尝试以下问题：

- 某个药品可以长期服用吗？
- 忘记服药应该怎么处理？
- 某类药物适合哺乳期使用吗？

## 评测

项目已预留基础评测目录，可先从检索层开始量化：

```bash
python eval/run_eval.py
```

也可以给评测设置最低阈值，适合放进 CI：

```bash
python eval/run_eval.py --min-retrieval-hit-rate 0.6 --min-keyword-coverage-rate 0.4
```

当前脚本会读取 [eval/qa_dataset.jsonl](/e:/agent/medagent/eval/qa_dataset.jsonl) 中的样本，对检索结果做基础统计，包括：

- 检索命中率
- 来源命中率
- 关键词覆盖率

评测说明见 [eval/README.md](/e:/agent/medagent/eval/README.md)。

Answer-level 评测脚本：

```bash
python eval/run_answer_eval.py --provider minimax --api-key your-minimax-key
```

## 测试

项目当前提供基础单元测试，可直接执行：

```bash
python -m pytest
```

覆盖范围包括：

- provider 配置读取
- markdown memory 持久化
- 来源拼接
- 医疗知识库和个人信息库独立开关
- 回答依据和参考来源折叠渲染
- 章节级切分、通用相关性门控和低相关片段过滤
- 检索回退逻辑
- 知识库上传、预览和删除
- OCR 状态检测与降级

## 日志与指标

每次问答会将基础运行指标写入 `logs/chat_metrics.jsonl`，便于后续做简单分析。

当前落盘字段包括：

- `provider`
- `embedding_provider`
- `question_redacted`
- `knowledge_hit`
- `knowledge_bases_hit`
- `medical_knowledge_enabled`
- `personal_knowledge_enabled`
- `retrieved_doc_count`
- `source_labels`
- `fallback_used`
- `status`
- `error_type`
- `risk_level`
- `risk_flags`
- `duration_ms`

默认会对日志中的问题文本做脱敏处理，避免手机号、邮箱、身份证号等直接落盘。

## 已知限制

- 项目定位为技术演示，医疗问题应结合医生或药师意见。
- 当前知识库内容较少，答案质量高度依赖样本覆盖。
- 各 Provider 的模型能力和兼容性存在差异。
