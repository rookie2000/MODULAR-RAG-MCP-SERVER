# Modular RAG MCP Server 深度教程

这份教程面向想真正读懂、跑通、讲清楚、并能二次开发本项目的学习者。它不是 `teach.md` 的简单改写，而是按当前仓库代码重新梳理：先理解系统定位，再跑通主流程，然后沿源码拆解架构、核心实现、学习路线和扩展方式。

本项目的核心价值是把 RAG 工程中的关键能力放在一个可运行、可观测、可扩展的系统里：文档摄取、PDF 解析、文本切分、元数据增强、图片描述、Dense Embedding、BM25 稀疏索引、Chroma 向量库、混合检索、RRF 融合、可选重排、MCP 工具暴露、Streamlit Dashboard 和评估体系。

如果你准备面试大模型应用、RAG 工程、MCP 工具开发，或者想把这个项目改造成自己的知识库服务，请按本文的学习路径推进。

## 1. 项目定位

`modular-rag-mcp-server` 是一个模块化 RAG MCP Server。它不是单纯的问答 Demo，而是一个工程化骨架：

- 对外通过 MCP 暴露工具，供 Claude Desktop、GitHub Copilot 或其他 MCP Client 调用。
- 对内通过离线摄取流水线把 PDF 等资料转成可检索知识库。
- 查询时同时走 Dense 语义检索和 Sparse BM25 关键词检索，再通过 RRF 融合结果。
- 通过 Trace、Dashboard 和 Evaluation 让 RAG 链路可观察、可调试、可评估。
- 通过 `src/libs/` 下的接口和工厂模式，让 LLM、Embedding、Reranker、Vector Store 等能力可替换。

一句话概括：这是一个把 RAG 关键工程问题串起来的 MCP 知识库服务。

## 2. 技术栈总览

项目使用 Python 3.10+。依赖和开发工具集中在 `pyproject.toml`：

| 类型 | 技术 | 在项目中的作用 |
| --- | --- | --- |
| MCP | `mcp>=1.0.0` | 通过 stdio transport 暴露 MCP tools |
| 配置 | `pyyaml` | 加载 `config/settings.yaml` |
| 文档解析 | `markitdown[pdf]` | PDF 转文本，配合图片抽取 |
| 文本切分 | `langchain-text-splitters` | Recursive splitter |
| 向量库 | `chromadb` | Dense 向量持久化和相似度查询 |
| 中文分词 | `jieba` | BM25 稀疏检索中的中文关键词处理 |
| Dashboard | `streamlit` | 可视化管理和 Trace 查看 |
| 评估 | `ragas`, `datasets` | RAG 评估能力 |
| 测试 | `pytest`, `pytest-asyncio`, `pytest-mock`, `pytest-cov` | 单元、集成、端到端测试 |
| 质量 | `ruff`, `mypy` | Lint 和类型检查 |

项目默认配置在 `config/settings.yaml`，包含 LLM、Embedding、Vision LLM、Vector Store、Retrieval、Rerank、Evaluation、Observability、Ingestion 等配置块。

## 3. 目录结构

先记住这几个目录：

```text
.
├── main.py                         # 简单入口，主要做配置加载检查
├── config/
│   ├── settings.yaml               # 主配置
│   └── prompts/                    # LLM 相关 prompt
├── scripts/
│   ├── ingest.py                   # 摄取文档
│   ├── query.py                    # 本地查询
│   ├── start_dashboard.py          # 启动 Dashboard
│   └── evaluate.py                 # 运行评估
├── src/
│   ├── mcp_server/                 # MCP Server 和 tools
│   ├── ingestion/                  # 离线摄取流水线
│   ├── core/                       # 查询、响应、配置、Trace、核心类型
│   ├── libs/                       # 可插拔能力实现
│   └── observability/              # 日志、评估、Dashboard
└── tests/
    ├── unit/
    ├── integration/
    ├── e2e/
    └── fixtures/
```

理解项目时不要从文件数量最多的地方开始，而是先抓住两条主链路：

1. 离线摄取：文件进入系统，变成向量库和 BM25 索引。
2. 在线查询：用户问题进入系统，检索、融合、重排，然后返回结果。

## 4. 整体架构

可以把系统分成六层：

```text
MCP Client
   |
   | JSON-RPC over stdio
   v
MCP Server
   |
   | tool call
   v
Core Query Engine
   |
   | dense + sparse + fusion + rerank
   v
Storage Layer
   |
   | Chroma + BM25 + image index
   v
Ingestion Pipeline
   |
   | load + split + transform + embed + upsert
   v
Documents
```

旁路还有两类能力：

- `observability`：记录日志、Trace、Dashboard 页面。
- `evaluation`：用 golden test set 或 Ragas/custom evaluator 做回归评估。

这套架构的重点不是某个算法多复杂，而是模块边界清楚：摄取、检索、协议、配置、可观测性、评估各自独立，同时又能被脚本和 MCP tool 串起来。

## 5. 快速跑通项目

### 5.1 安装依赖

建议使用 `uv` 创建项目内独立环境，避免和本机已经用 `pip install` 安装过的包互相影响：

```bash
uv sync --extra dev
```

这会在项目根目录创建 `.venv/`，并把运行依赖和测试、lint、类型检查工具都安装到这个隔离环境里。Windows 下也可以直接运行：

```powershell
.\scripts\setup_env.ps1
```

后续命令建议统一用 `uv run ...` 执行，确保使用的是当前项目的 `.venv`。

### 5.2 检查配置

主配置文件是：

```text
config/settings.yaml
```

关键配置包括：

- `llm.provider`：支持 `openai`、`azure`、`ollama`、`deepseek`、`minimax`。
- `embedding.provider`：支持 `openai`、`azure`、`ollama`、`minimax`。
- `vision_llm.enabled`：是否启用图片描述。
- `vector_store.provider`：当前主要实现是 `chroma`。
- `retrieval.dense_top_k`、`sparse_top_k`、`fusion_top_k`、`rrf_k`：控制混合检索。
- `rerank.enabled`：是否启用重排。
- `observability.trace_enabled`：是否开启 Trace。
- `ingestion.chunk_size`、`chunk_overlap`、`batch_size`：控制摄取流水线。

注意不要把真实 API Key 提交到仓库。可以参考 `config/test_credentials.yaml.example` 管理本地凭证。

### 5.3 摄取文档

可以先用测试夹具中的 PDF：

```bash
uv run python scripts/ingest.py --path tests/fixtures/sample_documents/simple.pdf --collection demo
```

处理目录：

```bash
uv run python scripts/ingest.py --path tests/fixtures/sample_documents --collection demo
```

强制重新处理：

```bash
uv run python scripts/ingest.py --path tests/fixtures/sample_documents/simple.pdf --collection demo --force
```

预览将处理哪些文件但不执行摄取：

```bash
uv run python scripts/ingest.py --path tests/fixtures/sample_documents --dry-run
```

### 5.4 本地查询

摄取完成后执行：

```bash
uv run python scripts/query.py --query "这个文档讲了什么" --collection demo --verbose
```

`--verbose` 会打印 Dense、Sparse、Fusion 等中间结果，适合学习和调试。

禁用重排：

```bash
uv run python scripts/query.py --query "RRF 是什么" --collection demo --no-rerank
```

### 5.5 启动 Dashboard

```bash
uv run python scripts/start_dashboard.py --port 8501
```

Dashboard 对应源码在：

```text
src/observability/dashboard/app.py
src/observability/dashboard/pages/
src/observability/dashboard/services/
```

它用于查看系统概览、数据浏览、摄取管理、摄取 Trace、查询 Trace 和评估面板。

### 5.6 运行评估

使用默认 golden test set：

```bash
uv run python scripts/evaluate.py
```

不连接检索系统，只验证评估框架：

```bash
uv run python scripts/evaluate.py --no-search
```

指定集合：

```bash
uv run python scripts/evaluate.py --collection demo
```

## 6. 配置驱动架构

配置加载核心在：

```text
src/core/settings.py
```

这个文件定义了多个 dataclass：

- `LLMSettings`
- `EmbeddingSettings`
- `VectorStoreSettings`
- `RetrievalSettings`
- `RerankSettings`
- `EvaluationSettings`
- `ObservabilitySettings`
- `VisionLLMSettings`
- `IngestionSettings`
- `Settings`

`Settings.from_dict()` 会校验 `settings.yaml` 的结构和字段类型。这样做的好处是：

1. 启动早期就能发现配置错误。
2. 业务代码不用反复处理裸字典。
3. 工厂类可以根据 provider 动态创建实现。
4. 测试可以直接构造 Settings 对象验证不同配置。

`resolve_path()` 会把相对路径解析到仓库根目录，避免脚本从不同工作目录启动时找不到数据目录。

## 7. MCP Server 实现

MCP Server 的正式入口在：

```text
src/mcp_server/server.py
```

它做了几件重要的工程处理：

1. 使用官方 MCP SDK 的 stdio transport。
2. 把日志重定向到 stderr，因为 stdout 要专门留给 JSON-RPC 协议消息。
3. 预加载 `chromadb` 和部分内部模块，避免后台线程中 lazy import 触发 import lock 问题。
4. 调用 `create_mcp_server()` 创建低层 MCP Server。

工具注册逻辑在：

```text
src/mcp_server/protocol_handler.py
```

核心类是 `ProtocolHandler`。它负责：

- 保存工具注册表。
- 把工具定义转成 MCP `types.Tool` schema。
- 根据工具名执行 handler。
- 把字符串、列表、`CallToolResult` 等返回值统一包装成 MCP 结果。
- 捕获参数错误和内部错误，避免直接泄露堆栈。

默认注册的工具有三个：

```text
src/mcp_server/tools/query_knowledge_hub.py
src/mcp_server/tools/list_collections.py
src/mcp_server/tools/get_document_summary.py
```

它们分别对应：

- `query_knowledge_hub`：主查询入口。
- `list_collections`：列出可用集合。
- `get_document_summary`：获取文档摘要或元信息。

### 7.1 为什么 stdout 不能写日志

MCP stdio 模式下，客户端和服务端通过标准输入输出交换 JSON-RPC 消息。如果普通日志写到 stdout，客户端会把日志当成协议消息解析，从而导致通信损坏。所以 `server.py` 中专门把 logging handler 指向 stderr。

这是一个非常适合面试讲的工程细节：协议通道和日志通道必须隔离。

## 8. 离线摄取流水线

摄取主类在：

```text
src/ingestion/pipeline.py
```

`IngestionPipeline` 把一个 PDF 处理成可检索资产。它的 `run()` 方法包含六个阶段：

```text
1. File Integrity Check
2. Document Loading
3. Document Chunking
4. Transform Pipeline
5. Encoding
6. Storage
```

### 8.1 Stage 1: 文件完整性检查

组件：

```text
src/libs/loader/file_integrity.py
```

它基于 SHA256 判断文件是否已成功处理。默认记录到：

```text
data/db/ingestion_history.db
```

如果文件没有变化并且未使用 `--force`，流水线会跳过，保证摄取幂等。

这个设计解决了 RAG 工程中常见的重复入库问题。

### 8.2 Stage 2: 文档加载

组件：

```text
src/libs/loader/pdf_loader.py
```

`PdfLoader` 负责把 PDF 转为 `Document`，同时抽取图片并保存到：

```text
data/images/<collection>/
```

文档统一使用核心类型，定义在：

```text
src/core/types.py
```

这种统一类型很重要，因为后续 chunking、transform、embedding、storage 都围绕这些类型传递。

### 8.3 Stage 3: 文本切分

组件：

```text
src/ingestion/chunking/document_chunker.py
src/libs/splitter/
```

默认 splitter 是 `recursive`，配置来自：

```yaml
ingestion:
  chunk_size: 1000
  chunk_overlap: 200
  splitter: "recursive"
```

切分阶段的核心目标不是简单截断文本，而是保持语义连续性，并保留 source path、chunk index、page info 等 metadata，方便后续引用和调试。

### 8.4 Stage 4: Transform Pipeline

包含三个子阶段：

```text
src/ingestion/transform/chunk_refiner.py
src/ingestion/transform/metadata_enricher.py
src/ingestion/transform/image_captioner.py
```

职责分别是：

- `ChunkRefiner`：优化 chunk 文本质量，可用规则或 LLM。
- `MetadataEnricher`：补充标题、标签、摘要等元数据。
- `ImageCaptioner`：调用 Vision LLM 为图片生成文本描述，让图片内容也能进入文本检索链路。

这些 transform 都支持降级：LLM 不可用时可以回退到规则处理，避免整条摄取流水线因为某个模型调用失败而中断。

### 8.5 Stage 5: Dense 和 Sparse 编码

组件：

```text
src/ingestion/embedding/dense_encoder.py
src/ingestion/embedding/sparse_encoder.py
src/ingestion/embedding/batch_processor.py
```

Dense 编码调用 Embedding provider，把文本转为向量。Embedding 实现由工厂创建：

```text
src/libs/embedding/embedding_factory.py
```

Sparse 编码统计 BM25 需要的词频、文档长度、关键词信息。对于中文内容，项目使用 `jieba` 辅助分词。

`BatchProcessor` 把 Dense 和 Sparse 编码组织成批处理，提高吞吐并统一输出。

### 8.6 Stage 6: 存储

包含三类存储：

```text
src/ingestion/storage/vector_upserter.py
src/ingestion/storage/bm25_indexer.py
src/ingestion/storage/image_storage.py
```

分别负责：

- ChromaDB 向量写入。
- BM25 索引构建和持久化。
- 图片文件索引登记。

一个关键细节是：BM25 的 `chunk_id` 会对齐 Chroma 中的 vector id。这样 Sparse 检索命中后，可以回到向量库取完整 chunk 和 metadata。

## 9. 在线查询链路

查询脚本入口是：

```text
scripts/query.py
```

它会构建这些组件：

```text
VectorStoreFactory
EmbeddingFactory
DenseRetriever
BM25Indexer
SparseRetriever
QueryProcessor
HybridSearch
Core Reranker
```

主查询流程如下：

```text
query
  |
  v
QueryProcessor
  |
  v
DenseRetriever       SparseRetriever
  |                  |
  v                  v
dense results       sparse results
  \                  /
   v                v
       RRFFusion
          |
          v
       optional rerank
          |
          v
       final results
```

## 10. Hybrid Search 核心实现

核心文件：

```text
src/core/query_engine/hybrid_search.py
```

`HybridSearch.search()` 是在线检索的中心。它做了六步：

1. 校验 query 不能为空。
2. 用 `QueryProcessor` 提取关键词和 filters。
3. 同时执行 Dense 和 Sparse 检索。
4. 如果一条检索路径失败，则回退到另一条。
5. 如果两条都成功，则用 RRF 融合。
6. 应用 metadata filter，并截取 top_k。

### 10.1 Dense Retrieval

Dense Retrieval 的输入是原始 query。流程是：

```text
query -> embedding -> vector store similarity search -> RetrievalResult[]
```

它擅长处理语义相近但字面不完全一致的问题，比如“怎么配置 Azure OpenAI”和“Azure 模型接入步骤”。

### 10.2 Sparse Retrieval

Sparse Retrieval 的输入是关键词列表。流程是：

```text
query -> keywords -> BM25 index search -> chunk ids -> vector store fetch -> RetrievalResult[]
```

它擅长处理专有名词、精确术语、代码标识符、配置字段等，例如 `rrf_k`、`deployment_name`、`query_knowledge_hub`。

### 10.3 RRF 融合

RRF 全称 Reciprocal Rank Fusion。它不依赖不同检索器的原始分数是否可比较，而是根据排名做融合：

```text
score(doc) = sum(1 / (k + rank_i))
```

其中 `k` 默认是 60，来自：

```yaml
retrieval:
  rrf_k: 60
```

RRF 的好处是简单、稳定、容易解释。Dense 和 Sparse 的分数尺度可能完全不同，但排名可以统一融合。

### 10.4 Fallback 设计

`HybridSearch` 对 Dense 和 Sparse 都有错误捕获。如果 Dense 失败但 Sparse 成功，就用 Sparse 结果；如果 Sparse 失败但 Dense 成功，就用 Dense 结果；如果两者都失败，才抛出错误。

这体现了 RAG 工程的一个原则：单个组件失败不应该轻易拖垮整个系统，尤其是检索链路可以自然降级。

## 11. Rerank 与响应构造

Rerank 配置在：

```yaml
rerank:
  enabled: false
  provider: "none"
  model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
  top_k: 5
```

相关代码位于：

```text
src/core/query_engine/reranker.py
src/libs/reranker/
```

项目支持不同重排方式：

- `none`：直接使用融合结果。
- `cross_encoder`：本地交叉编码器重排。
- `llm`：用 LLM 判断相关性。

响应构造相关模块在：

```text
src/core/response/
```

包括：

- `response_builder.py`：构造最终回答结构。
- `citation_generator.py`：生成引用信息。
- `multimodal_assembler.py`：处理多模态内容组合。

学习时可以先掌握检索链路，再读响应构造。因为回答质量通常由“检索是否命中正确上下文”和“生成是否忠实引用上下文”共同决定。

## 12. 可插拔 Provider 设计

项目的可插拔能力集中在：

```text
src/libs/
```

典型结构是：

```text
src/libs/embedding/
├── base_embedding.py
├── openai_embedding.py
├── azure_embedding.py
├── ollama_embedding.py
├── minimax_embedding.py
└── embedding_factory.py
```

这种结构在 LLM、Embedding、Reranker、Splitter、Vector Store、Evaluator 中反复出现。

设计套路是：

1. 定义 base interface。
2. 每个 provider 一个实现文件。
3. 工厂类读取 `settings.provider`。
4. 调用方只依赖抽象接口，不关心具体 provider。

如果你要新增一个 provider，例如 `qwen_embedding`，建议按这个流程：

1. 在 `src/libs/embedding/` 新增实现类。
2. 继承或遵守 `base_embedding.py` 的接口。
3. 在 `embedding_factory.py` 注册 provider 名称。
4. 在 `config/settings.yaml` 中增加配置示例。
5. 在 `tests/unit/` 增加 factory 和 smoke test。

这就是项目可扩展性的核心。

## 13. 可观测性与 Trace

RAG 系统难调试的原因是链路长：加载、切分、改写、向量化、入库、检索、融合、重排、生成，每一步都可能影响最终结果。

本项目用 Trace 记录中间状态：

```text
src/core/trace/
src/observability/dashboard/services/trace_service.py
```

在摄取流水线中，`pipeline.py` 会记录：

- load 阶段的文本长度、图片数量、预览文本。
- split 阶段的 chunk 数、平均长度、chunk 内容。
- transform 阶段的 refine/enrich/caption 结果。
- embed 阶段的向量数量、维度、稀疏词频信息。
- upsert 阶段的 Chroma、BM25、图片索引写入情况。

在查询链路中，`hybrid_search.py` 会记录：

- query processing 的关键词。
- dense retrieval 的结果数量、分数、chunk。
- sparse retrieval 的关键词和命中。
- fusion 的输入列表和融合结果。

这些 Trace 是做 RAG 调优的基础。不要只看最终答案，要看每个阶段是否把正确内容传给了下一阶段。

## 14. Dashboard

Dashboard 基于 Streamlit：

```text
src/observability/dashboard/app.py
src/observability/dashboard/pages/
```

页面包括：

- `overview.py`：系统概览。
- `data_browser.py`：数据浏览。
- `ingestion_manager.py`：摄取管理。
- `ingestion_traces.py`：摄取链路 Trace。
- `query_traces.py`：查询链路 Trace。
- `evaluation_panel.py`：评估面板。

服务层在：

```text
src/observability/dashboard/services/
```

Dashboard 的意义不是做一个漂亮界面，而是把 RAG 内部状态暴露出来。对于学习者来说，它可以帮助你理解每一步的输入输出；对于工程团队来说，它是排查召回差、答案幻觉、数据缺失的入口。

## 15. Evaluation 评估体系

评估入口：

```text
scripts/evaluate.py
```

默认测试集：

```text
tests/fixtures/golden_test_set.json
```

评估相关源码：

```text
src/libs/evaluator/
src/observability/evaluation/
```

项目支持 custom evaluator 和 Ragas evaluator。常见指标包括：

- `hit_rate`：正确 chunk 是否被召回。
- `mrr`：正确结果排名是否靠前。
- `faithfulness`：回答是否忠实于上下文。

真正做 RAG 不能只靠主观试问。你需要构造 golden set，把一组固定问题和期望命中文档作为回归集。每次改 splitter、embedding、rerank、prompt，都跑一次评估，避免“看起来变好，实际召回变差”。

## 16. 测试体系

测试目录：

```text
tests/unit/
tests/integration/
tests/e2e/
tests/fixtures/
```

pytest 配置在 `pyproject.toml`：

```toml
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "unit",
    "integration",
    "e2e",
    "llm",
    "slow",
]
```

常用命令：

```bash
uv run pytest
uv run pytest tests/unit
uv run pytest -m "not llm"
uv run pytest tests/integration/test_hybrid_search.py
```

推荐学习顺序：

1. 先读 `tests/unit/test_config_loading.py`，理解配置校验。
2. 再读 `tests/unit/test_fusion_rrf.py`，理解 RRF。
3. 再读 `tests/unit/test_vector_store_contract.py`，理解向量库接口。
4. 再读 `tests/integration/test_ingestion_pipeline.py`，理解完整摄取。
5. 最后读 `tests/e2e/test_mcp_client.py`，理解端到端使用方式。

测试是理解系统边界的捷径。一个模块的测试通常比模块本身更快告诉你“作者期望它怎么用”。

## 17. 学习路线

### 17.1 路线一：快速上手

适合只想跑通项目的人：

1. 阅读 `README.md` 和本文前 6 节。
2. 安装依赖。
3. 配置 `config/settings.yaml`。
4. 用 `scripts/ingest.py` 摄取一个测试 PDF。
5. 用 `scripts/query.py --verbose` 查询。
6. 启动 Dashboard 查看 Trace。

目标：知道系统能做什么，能完成一次完整摄取和查询。

### 17.2 路线二：RAG 工程学习

适合准备面试或系统学习 RAG 的人：

1. 读 `src/ingestion/pipeline.py`，画出六阶段摄取流程。
2. 读 `src/core/query_engine/hybrid_search.py`，理解混合检索。
3. 读 `src/core/query_engine/fusion.py`，手算一个 RRF 例子。
4. 读 `src/ingestion/storage/bm25_indexer.py`，理解稀疏索引如何保存。
5. 读 `src/libs/vector_store/chroma_store.py`，理解向量库抽象。
6. 跑 `scripts/query.py --verbose`，对照输出理解每个阶段。

目标：能解释 Dense、Sparse、RRF、Rerank、Trace 各自解决什么问题。

### 17.3 路线三：MCP 工具开发

适合想把能力暴露给 AI Agent 的人：

1. 读 `src/mcp_server/server.py`。
2. 读 `src/mcp_server/protocol_handler.py`。
3. 读 `src/mcp_server/tools/query_knowledge_hub.py`。
4. 理解 tool schema、handler、`CallToolResult`。
5. 仿照现有 tools 新增一个只读工具，例如 `get_collection_stats`。

目标：能独立新增一个 MCP tool，并理解 stdio 协议注意事项。

### 17.4 路线四：二次开发

适合想改造成自己项目的人：

1. 先确定要替换哪一层：LLM、Embedding、Vector Store、Reranker、Loader 还是 Dashboard。
2. 在 `src/libs/<capability>/` 中新增 provider。
3. 在 factory 中注册。
4. 在 `config/settings.yaml` 增加配置。
5. 写 unit test 验证 factory。
6. 写 integration test 验证真实调用或 mock 调用。

目标：不破坏主链路，只替换一个可插拔模块。

## 18. 核心面试讲法

如果面试官问“你的 RAG 项目是怎么设计的”，可以这样回答：

第一层是离线摄取。我把 PDF 通过 loader 转成统一 Document，然后用 splitter 切成 chunk，再通过 refiner、metadata enricher、image captioner 做增强，最后同时生成 dense embedding 和 BM25 sparse stats，分别写入 Chroma 和 BM25 索引。

第二层是在线检索。查询进入后先做 query processing，然后并行执行 Dense 语义检索和 Sparse 关键词检索。两路结果用 RRF 融合，因为它不依赖不同检索器原始分数的尺度，工程上更稳定。融合后可以接 CrossEncoder 或 LLM reranker。

第三层是服务暴露。我用 MCP stdio server 把查询、列集合、文档摘要等能力暴露成工具。这里要保证 stdout 只输出 JSON-RPC 协议消息，日志必须走 stderr。

第四层是可观测和评估。摄取和查询每个阶段都会记录 Trace，Dashboard 可以看中间结果。评估侧用 golden test set 做 hit rate、MRR、faithfulness 等指标，避免只靠人工感觉调参。

这个回答能覆盖 RAG 工程里的数据、检索、协议、可观测性和评估五个重点。

## 19. 常见扩展任务

### 19.1 新增 MCP Tool

参考：

```text
src/mcp_server/tools/list_collections.py
```

步骤：

1. 新建 tool 文件。
2. 定义 input schema。
3. 实现 async handler。
4. 提供 `register_tool(protocol_handler)`。
5. 在 `protocol_handler._register_default_tools()` 中注册。
6. 添加 `tests/unit/test_<tool_name>.py`。

### 19.2 新增 Dashboard 页面

参考：

```text
src/observability/dashboard/pages/
src/observability/dashboard/services/
```

步骤：

1. 在 `pages/` 新建页面。
2. 如果需要读取数据，在 `services/` 增加服务方法。
3. 在 app 导航中接入页面。
4. 为数据服务写单元测试。

### 19.3 新增 Evaluator

参考：

```text
src/libs/evaluator/base_evaluator.py
src/libs/evaluator/evaluator_factory.py
```

步骤：

1. 实现 evaluator 类。
2. 返回统一 metrics 字典。
3. 在 factory 中注册 provider。
4. 在 `config/settings.yaml` 增加 provider 示例。
5. 用 `scripts/evaluate.py --no-search` 验证评估链路。

## 20. 调参思路

RAG 调参不要随机改。建议顺序是：

1. 先确认数据是否成功摄取：看 chunk 数、图片数、向量数、BM25 docs。
2. 再确认查询是否召回：用 `scripts/query.py --verbose` 看 Dense 和 Sparse 结果。
3. 如果 Dense 差，检查 embedding provider、模型维度、chunk 长度。
4. 如果 Sparse 差，检查关键词、分词、BM25 索引和 collection。
5. 如果两路都有结果但排序差，调 `rrf_k`、`fusion_top_k` 和 rerank。
6. 如果召回正确但回答差，调 response builder 和 prompt。
7. 每次修改后跑 evaluation，不要只看单个 query。

经验上，RAG 的问题多数不是“模型不够强”，而是数据切分、索引、召回、过滤、引用链路某一步出了问题。

## 21. 当前代码中的注意点

1. `main.py` 目前主要是配置加载检查入口，不等于完整 MCP stdio server。正式 MCP server 在 `src/mcp_server/server.py`。
2. `config/settings.yaml` 中有占位 API Key，实际运行前需要替换成本地有效配置，且不要提交真实凭证。
3. `scripts/query.py` 依赖已经摄取的数据。如果没有先运行 ingest，查询会找不到相关文档。
4. LLM、Vision LLM、Embedding 调用可能依赖外部服务。测试时可使用 `uv run pytest -m "not llm"` 跳过真实模型调用。
5. 数据目录如 `data/db/chroma`、`data/db/bm25`、`data/images` 是运行时产物，不应和源码逻辑混淆。

## 22. 推荐阅读顺序

如果你只有一天时间：

1. `config/settings.yaml`
2. `scripts/ingest.py`
3. `src/ingestion/pipeline.py`
4. `scripts/query.py`
5. `src/core/query_engine/hybrid_search.py`
6. `src/core/query_engine/fusion.py`
7. `src/mcp_server/protocol_handler.py`
8. `src/mcp_server/server.py`

如果你有三天时间：

第一天跑通摄取和查询，理解配置和脚本。第二天读 ingestion 和 query engine，画出数据流。第三天读 MCP、Dashboard、Evaluation，并尝试新增一个 provider 或 tool。

如果你准备面试：

重点准备五个问题：

1. 为什么要 Dense + Sparse 混合检索？
2. RRF 为什么比直接加权分数更稳？
3. 如何保证摄取幂等？
4. MCP stdio 模式为什么要隔离 stdout 和 stderr？
5. 如何评估一次 RAG 改动是真的变好？

## 23. 总结

这个项目最值得学习的地方不是单个模型调用，而是完整工程链路：

- 用配置驱动组件组合。
- 用工厂和 base class 实现可插拔。
- 用摄取流水线把原始文档变成可检索资产。
- 用 Dense + Sparse + RRF 提高召回稳定性。
- 用 MCP 把能力交给 AI Client 调用。
- 用 Trace、Dashboard、Evaluation 让系统可解释、可调试、可迭代。

学完这个项目，你应该不只是会跑一个 RAG Demo，而是能回答：数据怎么进来、索引怎么建、查询怎么走、结果怎么融合、失败怎么降级、效果怎么评估、能力怎么暴露给 Agent。

这就是一个 RAG 工程项目从 Demo 走向可维护系统的关键。
