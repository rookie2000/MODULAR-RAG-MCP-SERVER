# Tool 设计与 Schema

## 当前 3 个 MCP tools

默认工具位于 `src/mcp_server/tools/`：

- `query_knowledge_hub.py`
- `list_collections.py`
- `get_document_summary.py`

这些工具通过各自的 `register_tool()` 注册到 `ProtocolHandler`。

## `list_collections`

用途：列出知识库中可用的 collection，帮助 Agent 先判断数据范围。

输入 schema：

```json
{
  "include_stats": {
    "type": "boolean",
    "default": true
  }
}
```

适合 Agent 什么时候调用：

- 用户没有说明查询哪个 collection。
- Agent 需要先发现系统里有哪些知识集合。
- 查询失败后，Agent 怀疑 collection 选错。

失败场景：

- ChromaDB 目录不存在。
- ChromaDB 依赖不可用。
- 持久化目录路径配置错误。

面试可讲点：这是一个发现类工具，参数少，风险低，适合作为 Agent 工作流的第一步。

## `query_knowledge_hub`

用途：对知识库执行混合检索，返回相关文档片段和引用。

输入 schema：

```json
{
  "query": {
    "type": "string"
  },
  "top_k": {
    "type": "integer",
    "default": 5,
    "minimum": 1,
    "maximum": 20
  },
  "collection": {
    "type": "string"
  }
}
```

适合 Agent 什么时候调用：

- 用户问的是知识库相关问题。
- Agent 需要外部事实或项目文档作为上下文。
- 第一次检索不够好时，可以换 query 或 collection 二次检索。

失败场景：

- `query` 为空。
- collection 没有数据。
- embedding provider 初始化失败。
- vector store 或 BM25 索引不可用。

面试可讲点：`top_k` 有最大值 20，这是很好的边界控制，避免 Agent 一次拿太多上下文造成延迟和 token 膨胀。

## `get_document_summary`

用途：根据 `doc_id` 获取文档摘要、title、tags、source path 和 chunk count。

输入 schema：

```json
{
  "doc_id": {
    "type": "string"
  },
  "collection": {
    "type": "string"
  }
}
```

适合 Agent 什么时候调用：

- `query_knowledge_hub` 返回了相关 doc_id，Agent 想补充文档级上下文。
- 用户问某个文档整体内容，而不是某个片段。
- Agent 需要确认来源、标签或摘要。

失败场景：

- doc_id 不存在。
- collection 选错。
- Chroma 查询失败。

面试可讲点：这是一个补充上下文工具。它不替代检索，而是在检索命中文档后帮助 Agent 更好地组织回答。

## 好工具设计原则

### 参数少而清晰

Agent 不是人类 CLI 用户。参数越多，模型越容易填错。当前工具大多只有 1-3 个参数，比较适合模型调用。

### Schema 可被模型理解

字段名要直接表达意图，比如 `query`、`top_k`、`collection`。description 要告诉模型什么时候用、怎么填。

### 返回可引用

RAG tool 返回结果要能支持引用来源，否则 Agent 容易生成看似合理但无法追溯的回答。

### 错误不泄漏堆栈

`ProtocolHandler.execute_tool()` 捕获内部异常，只返回简化错误。面试时可以讲：工具错误要对 Agent 可理解，对系统安全不暴露内部细节。

### 有边界控制

`top_k` 设置了 `minimum` 和 `maximum`。这类限制能控制上下文规模、查询成本和服务负载。

### collection 做作用域控制

collection 相当于知识命名空间。Agent 通过 collection 限定检索范围，可以减少无关结果，也为未来权限控制打基础。

