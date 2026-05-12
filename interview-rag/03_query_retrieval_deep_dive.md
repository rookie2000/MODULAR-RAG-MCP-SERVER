# 查询与检索链路深入理解

## 入口

本地查询入口是 `scripts/query.py`：

```powershell
uv run python scripts/query.py --query "这个文档讲了什么" --collection demo --verbose
```

MCP 查询入口是 `src/mcp_server/tools/query_knowledge_hub.py`，工具名为：

```text
query_knowledge_hub
```

它暴露的主要参数是：

- `query`：用户问题，必填。
- `top_k`：返回结果数量，默认 5，最大 20。
- `collection`：限制查询的集合。

## 查询链路

```text
query.py / MCP tool
  -> 加载 settings.yaml
  -> 创建 embedding client 和 vector store
  -> 创建 DenseRetriever
  -> 创建 SparseRetriever
  -> 创建 HybridSearch
  -> Dense + Sparse 检索
  -> RRF 融合
  -> 可选 rerank
  -> 输出结果和引用
```

## Dense 检索

Dense 检索会把用户 query 转成 embedding，然后到 Chroma 里找向量相似的 chunk。

优点：

- 能处理同义表达。
- 能召回语义相关但字面不完全匹配的内容。

局限：

- 对数字、缩写、专有名词、配置项不一定稳定。
- 依赖 embedding 模型质量。
- 查询时也需要 embedding 调用，会有成本和延迟。

## Sparse 检索

Sparse 检索基于 BM25 和分词结果，更关注关键词匹配。

优点：

- 对专有名词、配置项、命令、错误码更敏感。
- 不依赖 embedding 模型理解语义。

局限：

- 不擅长同义表达。
- 对分词、停用词和文档表述比较敏感。

## RRF 融合

RRF 在 `src/core/query_engine/fusion.py` 中实现。核心公式是：

```text
RRF_score(d) = sum(1 / (k + rank(d)))
```

它使用排名位置，而不是原始分数。因此它适合融合不同评分体系，比如向量相似度和 BM25 分数。

当前配置：

```yaml
retrieval:
  dense_top_k: 20
  sparse_top_k: 20
  fusion_top_k: 10
  rrf_k: 60
```

`rrf_k` 越大，排名差异的影响越平滑；越小，靠前结果的优势更明显。

## Rerank

rerank 是在召回和融合之后，对候选结果做更精细排序。当前默认关闭：

```yaml
rerank:
  enabled: false
  provider: "none"
```

面试时可以这样讲：召回阶段追求覆盖，rerank 阶段追求排序精度。rerank 会增加延迟和成本，所以通常只对 top N 候选做。

## MCP tool 如何暴露查询能力

`query_knowledge_hub` 把 RAG 查询包装成 MCP tool。外部 MCP Client 不需要知道 Chroma、BM25、RRF 的细节，只需要传入 `query`、`top_k`、`collection`。

这类设计的价值是：

- 让知识库检索能力可以被 Claude Desktop、IDE、Agent 框架调用。
- 把复杂 RAG 链路封装成稳定工具接口。
- 让 Agent 不直接访问数据库，而是通过受控 tool 获取上下文。

## 面试回答模板

### 为什么要混合检索？

因为单一路径有盲区。Dense 检索能理解语义，但对关键词、数字和专有名词不一定稳定；BM25 对关键词非常强，但不理解同义表达。混合检索把两者结合起来，提高召回覆盖率，尤其适合企业知识库、技术文档这类既有语义问题又有大量术语的场景。

### RRF 解决什么问题？

RRF 解决的是多个检索结果列表如何融合的问题。Dense 和 BM25 的原始分数尺度不同，直接加权很难校准。RRF 只看每个文档在各自列表中的排名，用 `1 / (k + rank)` 累积分数，所以不需要做复杂归一化，工程上简单稳定。

### rerank 放在哪一步？

rerank 通常放在召回和融合之后。先用 dense、sparse 和 RRF 拿到一批候选，保证召回覆盖；再对 top candidates 用 cross-encoder 或 LLM reranker 做精排。这样成本可控，因为 rerank 不需要处理全量文档，只处理少量候选。

### top_k 参数如何影响效果和成本？

`dense_top_k` 和 `sparse_top_k` 越大，召回覆盖更高，但融合和后续 rerank 的候选更多，延迟也可能上升。`fusion_top_k` 决定最终进入后续阶段的结果数量，太小可能漏掉相关文档，太大又会增加 rerank 和回答阶段成本。所以 top_k 要结合评估指标和响应时间来调。

