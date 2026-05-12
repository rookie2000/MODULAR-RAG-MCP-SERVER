# 面试问题与参考回答

## 项目整体架构

### 这个项目解决什么问题？

它解决的是把本地文档构造成可检索知识库，并通过 MCP tool 给外部客户端提供查询能力的问题。核心链路包括文档摄取、chunk、embedding、向量库、BM25、混合检索、RRF 融合、可选 rerank、Trace、Dashboard 和 Evaluation。

### 你怎么快速理解一个别人写的 RAG 项目？

我会先找入口而不是直接读所有源码。这个项目我先看 `scripts/ingest.py`、`scripts/query.py` 和 `config/settings.yaml`，确认怎么跑起来。然后沿着两条主链路读：离线摄取看 `src/ingestion/pipeline.py`，在线查询看 `src/core/query_engine/`。最后再看 MCP tools、Dashboard、Evaluation 这些外围工程能力。

## RAG 基础与工程化

### RAG 的核心流程是什么？

离线阶段把文档解析、切块、向量化并建立索引；在线阶段把用户问题向量化，召回相关 chunk，然后把结果作为上下文交给模型或工具返回。工程上还要考虑文档更新、去重、召回质量、排序、评估、延迟、成本和可观测性。

### 这个项目工程化体现在哪里？

它不是把逻辑写在一个脚本里，而是拆成 provider、pipeline、query engine、MCP server、dashboard、evaluation。配置通过 `settings.yaml` 驱动，LLM、Embedding、Vector Store 都通过 factory 创建，方便切换实现。Trace 和 Dashboard 也让链路可调试。

## 摄取 Pipeline

### `scripts/ingest.py` 做了什么？

它是摄取命令行入口，负责解析参数、加载配置、发现 PDF 文件、支持 dry-run、初始化 `IngestionPipeline`，然后逐个文件处理并汇总结果。真正的业务流水线在 `src/ingestion/pipeline.py`。

### 如何避免重复摄取？

项目会对文件计算 SHA256 hash，并用 SQLite 记录处理历史。默认情况下，如果 hash 已成功处理过，就跳过。用户可以通过 `--force` 强制重跑。这能节省 embedding 和 LLM 成本，也避免重复写索引。

### 为什么目录摄取几分钟才完成？

目录里有多个 PDF，每个文件都要解析、切 chunk、可选 LLM refine、可选 metadata enrich、embedding，再写 Chroma 和 BM25。如果开启了 LLM 增强，chunk 越多调用越多，延迟和 token 成本都会上升。

## Chunk 策略

### `chunk_size` 怎么选？

我会先用默认值跑通，再基于效果调。chunk 太大，召回内容不够聚焦；chunk 太小，语义容易被切断，而且 embedding 数量和存储成本增加。`chunk_overlap` 能保留上下文，但太大也会造成重复。最终要用查询样例和评估指标验证。

### 为什么需要 overlap？

因为固定切块可能把一个完整语义切到两个 chunk 里。overlap 可以让边界附近的信息在相邻 chunk 中都出现，降低语义断裂导致的召回失败。

## Embedding 与向量库

### embedding 调用和普通 LLM 对话有什么区别？

embedding 是把文本转成向量，通常没有自然语言生成输出，成本一般低于完整对话。但它仍然按输入文本规模计费，也有网络延迟。这个项目里真正更像对话生成的是 chunk refine、metadata enrichment、rerank 或最终回答生成。

### 为什么用 Chroma？

Chroma 是本地持久化向量库，适合开发和小中规模 Demo。它降低了部署门槛，能快速验证 RAG 链路。生产环境可以通过 vector store factory 替换成 Qdrant、Pinecone 等。

## BM25 与中文分词

### BM25 在 RAG 中有什么作用？

BM25 是关键词检索，适合专有名词、命令、错误码、数字、配置项等精确匹配场景。它弥补了 dense embedding 在字面匹配上的不足。

### 中文场景为什么要关注分词？

BM25 依赖 term，如果中文没有合理分词，关键词统计会不稳定。这个项目依赖 `jieba`，说明它考虑了中文文档的 sparse 检索需求。

## Dense + Sparse + RRF

### 为什么 Dense 和 Sparse 都要做？

Dense 负责语义召回，Sparse 负责关键词召回。企业文档和技术文档里，两类需求都很多。混合检索能提高召回覆盖，降低单一路径漏召的风险。

### RRF 为什么适合融合？

因为 dense 分数和 BM25 分数不是一个尺度，直接加权需要调归一化。RRF 只看排名，不看原始分数，所以实现简单、稳定，也适合融合异构检索器。

## Rerank

### rerank 有什么价值？

召回阶段更关注覆盖，rerank 更关注 top 结果排序。它可以用更强但更慢的模型判断 query 和 chunk 的相关性，提高最终结果质量。

### rerank 的代价是什么？

代价是延迟和成本。尤其是 LLM rerank，每个候选都可能消耗 token。因此通常只对融合后的 top N 做 rerank，并通过评估确认收益。

## MCP 协议和 Tools

### MCP 在这个项目里起什么作用？

MCP 把知识库查询能力包装成标准 tool，外部客户端只需要调用 `query_knowledge_hub` 这类工具，不需要关心底层检索实现。这使 RAG 能力更容易接入 Agent 或 IDE。

### `query_knowledge_hub` 的输入是什么？

主要是 `query`、`top_k`、`collection`。它内部初始化检索组件，执行 hybrid search 和可选 rerank，最后构造带引用的响应。

## 可观测性、Trace、Dashboard

### 为什么 RAG 项目需要 Trace？

RAG 的问题经常不是模型本身，而是召回没召到、chunk 切得不好、融合排序不合理。Trace 能看到每个阶段输入输出，帮助定位问题。

### Dashboard 有什么价值？

Dashboard 能把摄取、查询、数据浏览、Trace、评估可视化。它让调试从看日志变成观察链路，对团队协作和演示都有帮助。

## Evaluation

### RAG 怎么评估？

可以评估检索和回答两个层面。检索层看 hit rate、MRR、top-k recall；回答层看 faithfulness、answer relevance 等。这个项目有 golden test set 和 evaluator 结构，适合做回归评估。

## 成本、性能、稳定性

### 如何降低成本？

可以关闭或减少摄取阶段的 LLM refine 和 metadata enrich，调小不必要的 top_k，控制 rerank 候选数量，使用缓存和文件 hash 去重，对大目录先 dry-run，再分批摄取。

### 如何提升稳定性？

要做参数校验、失败降级、日志和 trace、索引幂等写入、collection 隔离、测试覆盖。这个项目里的 hash 去重、hybrid search fallback、配置驱动都是稳定性设计的一部分。

## 如何改进这个项目

### 如果让你继续改，你会做什么？

我会优先做三类改进：第一，加一套参数实验和评估报告，把 chunk、top_k、rerank 的选择数据化；第二，增强文档更新和删除能力，保证 Chroma、BM25、图片索引一致；第三，完善生产化部署，比如认证、限流、异步任务队列和监控指标。

