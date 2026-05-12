# Demo 与 Debug 手册

## 本地启动 MCP Server

```powershell
uv run python -m src.mcp_server.server
```

注意：这是长期运行的 stdio server，适合被 MCP client 启动或手动调试。不要期待它像普通 CLI 那样打印很多人类可读输出，因为 stdout 是协议流。

## 运行 MCP 测试

E2E client 测试：

```powershell
uv run pytest tests/e2e/test_mcp_client.py -v
```

Integration 测试：

```powershell
uv run pytest tests/integration/test_mcp_server.py -v
```

这些测试会模拟 JSON-RPC 生命周期，验证 initialize、tools/list、tools/call 等协议行为。

## JSON-RPC 生命周期示例

initialize：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "clientInfo": {"name": "demo-client", "version": "0.1.0"},
    "capabilities": {}
  }
}
```

initialized notification：

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

tools/list：

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

tools/call：

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "query_knowledge_hub",
    "arguments": {
      "query": "这个项目有哪些 MCP tools？",
      "top_k": 3,
      "collection": "demo"
    }
  }
}
```

面试时不需要现场手搓完整客户端，可以展示测试文件如何模拟这些消息。

## 5-8 分钟面试 Demo 路线

1. 30 秒：说明这个项目从 Agent 角度是 MCP 工具服务。
2. 1 分钟：展示 `src/mcp_server/server.py`，讲 stdio、stdout/stderr 和 preload。
3. 1 分钟：展示 `src/mcp_server/protocol_handler.py`，讲 tools/list、tools/call、错误包装。
4. 1 分钟：展示 3 个 tools 的 schema。
5. 1-2 分钟：讲 Agent 如何 `list_collections -> query_knowledge_hub -> get_document_summary`。
6. 1 分钟：展示 e2e 测试，说明 wire-level 生命周期被覆盖。
7. 1 分钟：讲下一步 Agent 化：权限、结构化错误码、tool trace、demo agent client。

## 常见问题

### stdout 被日志污染

现象：MCP client 解析 JSON-RPC 失败。

原因：stdio transport 下 stdout 只能输出协议消息。

处理：日志写 stderr。当前项目已通过 `_redirect_all_loggers_to_stderr()` 处理。

### 工具参数错误

现象：`tools/call` 返回 `isError=True`，提示 invalid parameters。

原因：arguments 和 tool handler 不匹配，或者必填参数缺失。

处理：检查 `TOOL_INPUT_SCHEMA` 和 handler 签名。

### 没有 collection 数据

现象：`query_knowledge_hub` 返回空结果或提示未找到。

原因：还没有摄取文档，或查询 collection 和摄取 collection 不一致。

处理：先运行 ingest，或者调用 `list_collections` 确认可用集合。

### embedding provider 初始化失败

现象：query tool 初始化检索组件失败。

原因：provider 配置或 API key 缺失。

处理：检查 `config/settings.yaml` 和本地凭证。面试时可以说明这是外部模型服务依赖问题，不是 MCP 协议问题。

### MCP server 启动卡顿

可能原因：Chroma、onnxruntime、numpy 等重依赖加载较慢。项目已经通过 `_preload_heavy_imports()` 在主线程预加载，减少后续 tool call 线程 import 风险。

