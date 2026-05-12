# 下一步 Agent 化改造计划

本文件是面试时可以讲的“如果继续做，我会怎么把它从 MCP 工具服务推进成 Agent 应用”。本轮不实现这些功能，只作为项目打磨路线。

## P0：补齐工具权限分级

为什么做：Agent 工具不是同等风险。查询工具是只读，摄取和删除会改变系统状态，必须区分权限。

建议分级：

- Read-only：`list_collections`、`query_knowledge_hub`、`get_document_summary`
- Write：未来的 `ingest_document`
- Dangerous：未来的 `delete_document`、批量删除、执行外部命令

面试怎么讲：我会先把工具按风险分级，只读工具默认开放，写入工具需要显式确认，危险工具需要更严格的授权和审计。

优先级：高。

## P0：增加结构化错误码

为什么做：现在错误主要是文本。Agent 更适合消费结构化错误，比如 `COLLECTION_NOT_FOUND`、`EMPTY_QUERY`、`EMBEDDING_PROVIDER_ERROR`。

建议：

```json
{
  "ok": false,
  "error_code": "COLLECTION_NOT_FOUND",
  "message": "Collection 'demo' not found",
  "recoverable": true
}
```

面试怎么讲：结构化错误能帮助 Agent 做恢复策略，比如换 collection、提示先摄取、缩小 top_k。

优先级：高。

## P1：新增 `ingest_document` 工具

为什么做：当前摄取主要通过 CLI 和 Dashboard。Agent 如果要管理知识库，需要一个受控摄取工具。

关键边界：

- 限制 path 必须在允许目录内。
- 支持 `collection`。
- 默认 dry-run 或需要确认。
- 返回 file count、success、failed、trace id。

面试怎么讲：这是把 RAG 系统从查询工具扩展为知识库管理工具，但必须加路径限制和权限确认。

优先级：中高。

## P1：新增 `inspect_trace` 工具

为什么做：Agent 调试时需要知道上一次摄取或查询哪个阶段出了问题。

建议能力：

- 按 trace id 查询。
- 按 trace type 查询最近 N 条。
- 返回阶段摘要、耗时、错误、关键 metadata。

面试怎么讲：Agent 不只要能做事，还要能解释为什么失败。trace 工具能帮助 Agent 给出可诊断的反馈。

优先级：中。

## P1：新增 tool call trace

为什么做：当前项目有摄取和查询 trace，但 MCP tool call 层也值得记录。

建议记录：

- tool name
- arguments summary
- result summary
- latency
- isError
- error code
- collection

面试怎么讲：Agent 问题定位要看从工具选择到工具返回的完整链路，而不是只看 RAG 内部检索。

优先级：中。

## P2：新增 `evaluate_query` 工具

为什么做：让 Agent 或面试 Demo 能展示“检索效果可评估”。

建议能力：

- 输入 query、expected doc/chunk 或 golden set id。
- 输出 hit rate、MRR 或简化评估结果。

面试怎么讲：这能把 Agent 的工具使用从“能调通”推进到“能评估质量”。

优先级：中低。

## P2：增加 Agent demo client

为什么做：当前测试验证 MCP 协议，但没有一个面向演示的多步 Agent client。

建议流程：

```text
list_collections
  -> query_knowledge_hub
  -> get_document_summary
  -> final answer with citations
```

面试怎么讲：demo client 可以证明这个项目不只是 MCP server 能启动，而是能支撑 Agent 多步工具调用。

优先级：中。

## P2：增加安全策略

建议策略：

- collection allowlist
- path allowlist
- top_k hard limit
- sensitive metadata filtering
- write tools require confirmation
- per-tool timeout

面试怎么讲：Agent 连接真实系统时，最大的风险是越权和不可控动作。安全策略应该放在 tool 层，而不是只靠 prompt 约束模型。

优先级：中。

