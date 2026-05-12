# 项目理解

## 一句话定位

这是一个模块化 RAG MCP Server：离线把 PDF 文档摄取成可检索的知识库，在线通过 Dense + Sparse 混合检索和 RRF 融合返回相关片段，并通过 MCP tools 暴露给外部客户端使用。

## 面试视角下的核心价值

这个项目不是一个简单的 RAG Demo，而是一个工程化骨架。它把 RAG 应用常见的关键环节拆成清晰模块：

- 文档摄取：`scripts/ingest.py` 和 `src/ingestion/pipeline.py`
- PDF 解析：`src/libs/loader/pdf_loader.py`
- 文本切块：`src/ingestion/chunking/document_chunker.py`
- LLM 增强：`src/ingestion/transform/chunk_refiner.py`、`metadata_enricher.py`
- 图片描述：`src/ingestion/transform/image_captioner.py`
- Dense embedding：`src/ingestion/embedding/dense_encoder.py`
- Sparse BM25：`src/ingestion/embedding/sparse_encoder.py`、`src/ingestion/storage/bm25_indexer.py`
- 向量库：`src/libs/vector_store/chroma_store.py`
- 混合检索：`src/core/query_engine/hybrid_search.py`
- RRF 融合：`src/core/query_engine/fusion.py`
- 可选重排：`src/core/query_engine/reranker.py`
- MCP tools：`src/mcp_server/tools/`
- Dashboard：`src/observability/dashboard/`
- Trace 和评估：`src/core/trace/`、`src/observability/evaluation/`

## 两条主链路

离线摄取链路：

```text
PDF 文件
  -> ingest.py 解析参数
  -> IngestionPipeline
  -> 文件 hash 去重
  -> PDF 加载文本和图片
  -> 文本切 chunk
  -> LLM refine / metadata enrich / image caption
  -> Dense embedding + Sparse term stats
  -> Chroma 向量库 + BM25 索引 + 图片索引
```

在线查询链路：

```text
用户问题
  -> query.py 或 MCP tool
  -> QueryProcessor
  -> DenseRetriever 语义检索
  -> SparseRetriever BM25 关键词检索
  -> RRFFusion 融合排序
  -> 可选 Reranker
  -> ResponseBuilder 组织结果和引用
```

## 1 分钟介绍

我准备的这个项目是一个模块化 RAG MCP Server。它的核心是把 PDF 文档摄取到知识库里，然后对用户问题做 Dense 语义检索和 Sparse BM25 关键词检索，再用 RRF 做结果融合。工程上它还支持 Chroma 持久化、MCP 工具暴露、Trace、Dashboard 和 Evaluation，所以我主要把它当作一个 RAG 应用工程项目来理解和准备。

## 3 分钟介绍

这个项目分为离线摄取和在线查询两条链路。离线部分通过 `scripts/ingest.py` 启动，进入 `IngestionPipeline` 后先做文件 hash 去重，然后用 PDF loader 提取文本和图片，再按配置做 chunk。chunk 之后会经过可选的 LLM refine 和 metadata enrichment，然后生成 dense embedding，同时构建 sparse BM25 统计，最后分别写入 Chroma、BM25 索引和图片索引。

在线部分通过 `scripts/query.py` 或 MCP tool 调用。查询会先做预处理，然后并行走 dense retriever 和 sparse retriever。Dense 适合语义相似，Sparse 适合关键词、专有名词和精确匹配。两个结果列表用 RRF 融合，因为 RRF 不依赖原始分数尺度，适合把向量相似度和 BM25 这种不同分布的分数合并。之后可以接 rerank，再构造带引用的结果。

我关注这个项目的点主要是 RAG 工程化：模块边界、配置驱动、provider 工厂、可观测性、评估和成本控制。

## 5 分钟介绍

这个项目适合从 RAG 应用工程角度讲。首先，它不是只做一次问答，而是把知识库系统拆成可维护的模块。`src/libs/` 下抽象了 LLM、Embedding、Reranker、Vector Store、Splitter 等 provider；`src/ingestion/` 负责离线摄取；`src/core/query_engine/` 负责在线检索；`src/mcp_server/` 负责把能力通过 MCP 协议暴露出去；`src/observability/` 负责 Dashboard、Trace 和 Evaluation。

摄取阶段的关键工程问题是：如何把非结构化 PDF 变成可检索资产。项目里先用文件 hash 避免重复处理，再解析 PDF，按 `chunk_size` 和 `chunk_overlap` 切块。切块后可以用 LLM 做 chunk refinement 和 metadata enrichment，这会提升可读性和可检索元信息，但也带来 token 成本和延迟。编码阶段同时生成 dense vector 和 sparse stats，最后写入 Chroma 和 BM25。这样既能支持语义召回，也能支持关键词召回。

查询阶段的关键是召回质量和排序稳定性。Dense 检索能处理同义表达，但对专有名词和数字不一定稳定；BM25 对关键词敏感，但不理解语义。因此项目采用混合检索，并用 RRF 融合两个排序列表。RRF 的好处是只依赖 rank，不要求把向量分数和 BM25 分数归一化。后面如果开启 rerank，可以进一步提升 top 结果质量，但会增加延迟和成本。

从面试角度，我会强调我不是只会跑命令，而是理解了它为什么这样拆：配置驱动方便切 provider，MCP tool 让知识库能力能被外部 Agent 或客户端调用，Trace 和 Dashboard 让 RAG 链路可调试，Evaluation 让检索质量可以回归验证。

