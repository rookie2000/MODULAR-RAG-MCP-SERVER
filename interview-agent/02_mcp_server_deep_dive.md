# MCP Server 深入理解

## 关键文件

- `src/mcp_server/server.py`：MCP stdio server 入口。
- `src/mcp_server/protocol_handler.py`：工具注册、schema 暴露、工具调用和错误包装。
- `tests/e2e/test_mcp_client.py`：模拟 MCP client 的 wire-level 测试。
- `tests/integration/test_mcp_server.py`：stdio initialize 和 tools/list 集成测试。

## stdio transport 是什么

这个项目通过官方 MCP SDK 使用 stdio transport。客户端和服务器通过标准输入输出传递 JSON-RPC 消息：

```text
Client stdin/stdout <-> Server stdin/stdout
```

server 从 stdin 读请求，把响应写到 stdout。因为 stdout 是协议通道，所以不能写普通日志。

## 为什么日志要写 stderr

`server.py` 中 `_redirect_all_loggers_to_stderr()` 会把普通日志重定向到 stderr。

原因：MCP stdio 模式下，stdout 里的每一行都可能被客户端当成 JSON-RPC 消息解析。如果日志写到 stdout，客户端会收到非 JSON 内容，协议流就被污染。

面试表达：

MCP stdio 的 stdout 是协议通道，不是普通输出通道。这个项目把日志放到 stderr，是为了保证 wire protocol 干净。这是工具服务稳定性的细节。

## JSON-RPC 生命周期

典型生命周期：

```text
initialize
  -> server 返回 capabilities 和 serverInfo
notifications/initialized
  -> client 通知初始化完成
tools/list
  -> server 返回可用工具和 inputSchema
tools/call
  -> client 调用某个工具并传 arguments
```

`tests/e2e/test_mcp_client.py` 里模拟了这个流程，能帮助你理解真实客户端怎么和 server 交互。

## `_preload_heavy_imports()` 的价值

`server.py` 提前 import 了 `chromadb` 和一些内部查询模块。注释里解释了原因：MCP SDK 会使用 anyio 和后台线程处理 I/O，工具 handler 可能通过 `asyncio.to_thread()` 在线程里运行。如果在线程里第一次 lazy import Chroma、onnxruntime、numpy 等重依赖，可能和 stdin reader 线程竞争 Python import lock，导致卡住。

面试表达：

这是一个典型的工程稳定性优化。服务启动时在主线程预加载重依赖，让后续工具调用在线程里只命中 `sys.modules`，减少 import lock 死锁风险。

## `ProtocolHandler` 做了什么

`ProtocolHandler` 是工具协议层的核心：

- `register_tool()`：注册工具名、描述、input schema 和 handler。
- `get_tool_schemas()`：把工具注册表转成 MCP `types.Tool`，供 `tools/list` 返回。
- `execute_tool()`：根据工具名执行 handler，并统一包装返回。
- `get_capabilities()`：声明 server 能力。

错误处理：

- 工具不存在：返回 `isError=True`，提示 tool not found。
- 参数错误：捕获 `TypeError`，返回 invalid parameters。
- 内部错误：捕获通用异常，记录日志，但返回简化错误，不泄漏堆栈。

## `create_mcp_server()` 做了什么

`create_mcp_server()` 创建 low-level MCP `Server`，注册两个关键 handler：

- `@server.list_tools()`：处理 `tools/list`。
- `@server.call_tool()`：处理 `tools/call`。

默认工具通过 `_register_default_tools()` 注册：

- `query_knowledge_hub`
- `list_collections`
- `get_document_summary`

## 面试可讲总结

这个 MCP Server 的设计重点是把工具注册、协议处理和业务工具解耦。server 负责 stdio transport 和 MCP 生命周期，protocol handler 负责统一工具注册与调用，具体 tool 文件负责业务逻辑。这样的结构方便新增工具，也方便测试协议层和工具层。

