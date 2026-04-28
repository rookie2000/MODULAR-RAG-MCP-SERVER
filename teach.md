# Modular RAG MCP Server 项目教程

本教程详细讲解 Modular RAG MCP Server 的架构、技术栈和核心实现。

---

## 1. 项目概述

### 1.1 核心定位

本项目是一个基于 **多阶段检索增强生成 (RAG)** 与 **模型上下文协议 (MCP)** 设计的智能问答与知识检索框架。

**设计理念：自学与教学同步 (Learning by Teaching)**

- 实战驱动学习：项目架构本身就是 RAG 面试题的"活体答案"
- 开箱即用与深度扩展并重：提供 MCP 标准接口，可直接对接 Copilot/Claude
- 配套教学资源：技术文档 + 代码示范 + 视频讲解
- 学习路线与面试指南：知识点清单 + 高频面试题 + 简历撰写建议

### 1.2 功能特性

| 特性 | 说明 |
|------|------|
| **混合检索** | BM25 + Dense Embedding 双路召回 + RRF 融合 |
| **重排序** | 支持 None / Cross-Encoder / LLM Rerank 三种模式 |
| **MCP 接口** | 符合 JSON-RPC 2.0 标准的 Stdio 通信 |
| **可插拔架构** | LLM/Embedding/VectorStore/Splitter 均可配置切换 |
| **多模态处理** | PDF 解析 + 图片描述生成 + 双轨存储 |
| **可观测性** | 全链路 Trace + Streamlit Dashboard |
| **评估系统** | Ragas/DeepEval + 自定义指标 |

---

## 2. 技术架构

### 2.1 整体架构图

```
┌───────────────────────────────────────────────────────────────────┐
│                    MCP Clients (外部调用层)                           │
│         GitHub Copilot │ Claude Desktop │ 其他 MCP Agent                │
└────────────────────────────┬────────────────────────────────────┘
                             │ JSON-RPC 2.0 (Stdio)
                             ▼
┌───────────────────────────────────────────────────────────────────┐
│                      MCP Server 层                                │
│         tools/list, tools/call, resources/*                         │
│     query_knowledge_hub │ list_collections │ get_document_summary       │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌───────────────────────────────────────────────────────────────────┐
│                      Core 层 (核心业务)                            │
│  Query Engine: Processor → Hybrid Search → Reranker → Builder     │
│  Trace Collector: trace_id 生成 │ 各阶段耗时记录                  │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌───────────────────────────────────────────────────────────────────┐
│                      Storage 层                                  │
│       Vector Store (Chroma) │ BM25 Index │ Image Store            │
└────────────────────────────┬���───────────────────────────────────┘
                             ▼
┌───────────────────────────────────────────────────────────────────┐
│                 Ingestion Pipeline (离线数据摄取)                   │
│   Loader → Splitter → Transform → Embedding → Upsert            │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 分层架构说明

| 层级 | 主要模块 | 职责 |
|------|--------|------|
| **MCP Server 层** | server.py, protocol_handler.py, tools/* | 对外暴露的工具函数，协议解析与能力协商 |
| **Core 层** | query_engine/*, response/*, trace/* | 核心业务逻辑：检索、响应、追踪 |
| **Ingestion Pipeline** | pipeline.py, chunking/*, transform/*, embedding/*, storage/* | 离线数据摄取流水线 |
| **Libs 层** | llm/*, embedding/*, splitter/*, vector_store/* | 可插拔抽象层（工厂模式） |
| **Observability 层** | logger.py, dashboard/*, evaluation/* | 可观测性：日志、Dashboard、评估 |

---

## 3. 核心模块详解

### 3.1 混合检索引擎 (Hybrid Search)

**设计目标**：结合稠密向量和稀疏检索的优势，实现高精度召回。

**架构**：

```
用户查询
    │
    ▼
┌──────────────────────┐
│  Query Processor   │  关键词提取 │ 同义词扩展 │ Metadata 解析
└────────┬───────────┘
         │
    ┌────┴────┐
    ▼         ▼
Dense Route    Sparse Route    (并行执行)
(Embedding)   (BM25)
    │         │
    └────┬────┘
         ▼
   ┌────────────┐
   │ Fusion    │  RRF 融合算法
   │ (RRF)     │
   └────┬─────┘
        ▼
   ┌────────────┐
   │ Reranker   │  None / Cross-Encoder / LLM
   └────┬─────┘
        ▼
     返回结果
```

**RRF (Reciprocal Rank Fusion) 算法**：

```python
# 公式：Score = 1 / (k + Rank_Dense) + 1 / (k + Rank_Sparse)
# k 为平滑因子，通常取 k=60
```

### 3.2 MCP Server 实现

**通信方式**：Stdio 本地通信

- Client（Copilot/Claude Desktop）以子进程方式启动 Server
- 通过标准输入/输出交换 JSON-RPC 消息

**核心工具**：

| 工具名称 | 功能 |
|---------|------|
| `query_knowledge_hub` | 主检索入口，执行混合检索 + Rerank |
| `list_collections` | 列举知识库中可用的文档集合 |
| `get_document_summary` | 获取指定文档的摘要与元信息 |

**配置示例** (settings.yaml)：

```yaml
llm:
  provider: azure
  model: gpt-4o

embedding:
  provider: openai
  model: text-embedding-3-small

vector_store:
  backend: chroma
  persist_path: ./data/db/chroma

retrieval:
  sparse_backend: bm25
  fusion_algorithm: rrf
  top_k_dense: 20
  top_k_sparse: 20
  top_k_final: 10
```

### 3.3 可插拔架构设计

**设计原则**：

1. **接口隔离**：为每类组件定义最小化的抽象接口
2. **配置驱动**：通过 settings.yaml 指定各组件的后端
3. **工厂模式**：工厂函数根据配置动态实例化对应实现
4. **优雅降级**：首选后端不可用时自动回退

**可插拔组件**：

| 组件 | 默认实现 | 可替换选项 |
|------|---------|----------|
| LLM | Azure OpenAI | OpenAI / Ollama / DeepSeek |
| Embedding | OpenAI text-embedding-3 | BGE / Ollama 本地模型 |
| VectorStore | Chroma | Qdrant / Pinecone |
| Splitter | RecursiveCharacterTextSplitter | Semantic / FixedLen |
| Reranker | CrossEncoder | LLM Rerank / None |

---

## 4. 数据流详解

### 4.1 离线数据摄取流 (Ingestion Flow)

```
原始文档 (PDF)
      │
      ▼
┌─────────────────┐
│ File Integrity  │  SHA256 哈希检查，未变更则跳过
└────────┬────────┘
         │ 新文件/已变更
         ▼
┌─────────────────┐
│     Loader     │  PDF → Markdown + 元数据收集
│   (MarkItDown) │
└────────┬────────┘
         │ Document
         ▼
┌─────────────────┐
│    Splitter    │  语义切分，保留图片引用
│ (Recursive)   │
└────────┬────────┘
         │ Chunks[]
         ▼
┌─────────────────┐
│   Transform    │  LLM 重写 + 元数据注入 + 图片描述
└────────┬────────┘
         │ Enriched Chunks[]
         ▼
┌─────────────────┐
│   Embedding    │  Dense + Sparse 双路编码
└────────┬────────┘
         │ Vectors
         ▼
┌─────────────────┐
│    Upsert       │  Chroma + BM25 Index + 图片存储
└─────────────────┘
```

### 4.2 在线查询流 (Query Flow)

```
用户查询 (via MCP Client)
      │
      ▼
┌─────────────────┐
│  MCP Server    │  JSON-RPC 解析，工具路由
└────────┬────────┘
         │ query
         ▼
┌─────────────────┐
│ Query Processor │  关键词提取 + 同义词扩展
└────────┬────────┘
         │ processed_query
         ▼
┌─────────────────────────────────────┐
│         Hybrid Search              │
│   Dense Retrieval │ Sparse Retrieval │
└────────────┬──────────────────────┘
             │ Top-M 候选
             ▼
┌─────────────────┐
│    Reranker     │  CrossEncoder / LLM / None
└────────┬────────┘
         │ Top-K 精排
         ▼
┌─────────────────┐
│ Response Build │  引用生成 + MCP 格式化
└────────┬────────┘
         │
         ▼
    返回给 Client
```

---

## 5. 关键技术点

### 5.1 BM25 检索

**原理**：基于 TF-IDF 的概率检索模型

```python
# BM25 评分公式
score(Q, D) = Σ IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D| / avgdl))

# 其中：
# - f(qi, D): qi 在文档 D 中的词频
# - |D|: 文档长度
# - avgdl: 平均文档长度
# - k1, b: 调优参数 (通常 k1=1.5, b=0.75)
```

### 5.2 RRF 融合

**核心思想**：不依赖各路分数的绝对值，基于排名的倒数进行加权融合

```python
def rrf_fusion(results_list, k=60):
    """Reciprocal Rank Fusion"""
    scores = defaultdict(float)
    for results in results_list:
        for rank, doc in enumerate(results):
            scores[doc.id] += 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: -x[1])
```

### 5.3 Reranker

**三种模式**：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| None | 直接返回 RRF 结果 | 低延迟场景 |
| Cross-Encoder | 本地模型打分排序 | CPU 环境，M=10~30 |
| LLM Rerank | LLM 排序选择 | 需要强指令理解，M<=20 |

### 5.4 文件完整性检查 (Incremental Ingestion)

```python
# SHA256 哈希检查
file_hash = hashlib.sha256(file_content).hexdigest()

# 查询是否已处理
if check_file_integrity(file_hash) == "success":
    return  # 跳过，直接返回

# 处理完成后记录
save_file_integrity(file_hash, status="success")
```

---

## 6. 可观测性

### 6.1 Trace 追踪

**两类 Trace**：

1. **Query Trace**：记录查询全过程
   - query_processing → dense → sparse → fusion → rerank
   - 各阶段候选数量、分数分布、耗时

2. **Ingestion Trace**：记录摄取全过程
   - load → split → transform → embed → upsert
   - 各阶段耗时、chunk 数量、跳过/失败详情

### 6.2 Dashboard (Streamlit)

**六页面架构**：

| 页面 | 功能 |
|------|------|
| 系统总览 | 组件配置、数据资产统计 |
| 数据浏览器 | 文档列表、Chunk 详情、图片预览 |
| Ingestion 管理 | 触发摄取、删除文档 |
| Ingestion 追踪 | 摄取历史、阶段耗时瀑布图 |
| Query 追踪 | 查询历史、Dense/Sparse 对比 |
| 评估面板 | 运行评估、指标展示 |

---

## 7. 面试相关

### 7.1 高频面试题

| 问题 | 考察点 |
|------|--------|
| 为什么选择混合检索？ | RAG 核心理解 |
| RRF 和 weighted_sum 的区别？ | 融合算法原理 |
| Reranker 什么时候用？什么时候不用？ | 精度 vs 延迟权衡 |
| 如何做增量摄取？ | 工程实践 |
| 如何保证向量检索和 BM25 结果的一致性？ | 系统设计 |

### 7.2 简历撰写建议

**项目亮点**：

- 实现了 RAG 完整链路：Ingestion → Retrieval → Response
- 混合检索 + RRF 融合，提升召回率
- 可插拔架构，支持多 Provider 配置切换
- 全链路可观测，Trace + Dashboard
- MCP 协议对接，开箱即用

---

## 8. 学习资源

- 架构文档：`.claude/skills/auto-coder/references/05-architecture.md`
- 技术栈：`.claude/skills/auto-coder/references/03-tech-stack.md`
- 特性说明：`.claude/skills/auto-coder/references/02-features.md`

---

*本教程基于 Modular RAG MCP Server 项目文档整理*