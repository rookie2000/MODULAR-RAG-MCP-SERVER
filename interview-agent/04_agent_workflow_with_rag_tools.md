# Agent 如何使用 RAG Tools

## 基于现有工具的工作流

一个合理的 Agent 使用流程：

```text
用户问题
  -> 判断是否需要知识库
  -> list_collections
  -> 选择 collection
  -> query_knowledge_hub
  -> 检查结果是否足够
  -> 必要时改写 query 二次检索
  -> 必要时 get_document_summary
  -> 综合回答并引用来源
```

## 示例流程

用户问：“这个项目的 MCP 工具有哪些？怎么用？”

Agent 可以这样做：

1. 调用 `list_collections`，确认有哪些 collection。
2. 调用 `query_knowledge_hub`，query 设为 “MCP tools query_knowledge_hub list_collections get_document_summary”。
3. 如果结果里出现某个 doc_id，再调用 `get_document_summary` 获取文档级摘要。
4. 综合回答：列出工具、参数、使用场景和注意事项。

## Agent 和普通 RAG query 的区别

普通 RAG query 通常是一次性流程：

```text
query -> retrieve -> answer
```

Agent 使用工具时，多了决策过程：

- 是否需要查知识库。
- 查哪个 collection。
- query 怎么改写更适合检索。
- 一次检索不够时是否二次检索。
- 是否需要文档摘要补充上下文。
- 工具失败时是否换策略。

所以 Agent 工程里，RAG 不只是回答问题的后端，而是一个可组合工具。

## 上下文工程注意点

### 控制结果数量

`top_k` 太大，Agent 会拿到过多 chunk，容易增加 token 成本，也可能把无关内容带入回答。默认 5 是比较合理的起点。

### 保留引用

Agent 最终回答最好带来源。RAG tool 应该返回 source path、chunk id 或 citation 信息，帮助用户验证答案。

### 优先摘要，再展开

如果用户问文档整体内容，可以先用 `get_document_summary`，再根据需要调用 `query_knowledge_hub` 查细节。

### 避免无关 chunk 污染

Agent 不应该把所有检索结果都塞进最终回答。它需要筛选和总结，必要时说明“检索结果不足”。

### 工具结果要结构化

越结构化，Agent 越容易可靠使用。理想情况下，tool result 应包含 `content`、`citations`、`metadata`、`error_code`、`latency_ms` 等字段。

## 面试可讲案例

我会把这个项目里的 RAG 能力看成 Agent 的一个知识工具。Agent 不直接访问 Chroma 或 BM25，而是通过 MCP tool 调用。这样做的好处是边界清楚：工具负责检索和返回引用，Agent 负责规划、选择工具、组织答案。未来如果要加权限、审计、限流，也可以加在 MCP tool 层，而不是散落在 Agent prompt 里。

