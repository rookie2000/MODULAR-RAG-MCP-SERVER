# Agent/MCP 面试问题与参考回答

## Agent 基础

### Agent 和普通 Chatbot 有什么区别？

普通 Chatbot 主要是根据上下文生成回答。Agent 更强调能做决策和调用工具，比如判断是否需要检索、选择哪个工具、根据工具结果继续下一步。这个项目本身不是完整 Agent loop，但它提供了 Agent 能调用的 MCP 工具层。

### 你怎么理解 Agent 开发工程师？

我理解 Agent 开发工程师核心是把大模型接入真实系统能力。重点包括工具设计、上下文组织、错误恢复、权限边界、可观测性和评估，而不只是写 prompt。

## Tool Calling

### 好的 tool 应该长什么样？

好的 tool 参数要少而清晰，schema 要让模型容易理解，返回要结构化且可引用，错误要可恢复，还要有限制，比如 top_k 上限、路径限制和权限边界。当前项目的 `query_knowledge_hub` 就有 `top_k` 最大值，避免 Agent 一次请求过多上下文。

### 工具参数越多越好吗？

不是。参数越多，模型越容易填错，也越难判断何时使用。Agent 工具设计应该把复杂逻辑封装在工具内部，对模型暴露最少但足够的参数。

## MCP 协议

### MCP 在这个项目里做什么？

MCP 把知识库能力暴露成标准工具接口。外部 MCP client 可以先通过 `tools/list` 获取工具列表和 schema，再通过 `tools/call` 调用具体工具。这样 Agent 不需要知道底层 Chroma、BM25、RRF 的细节。

### MCP 和直接 HTTP API 有什么区别？

HTTP API 是通用通信方式，MCP 更面向模型上下文和工具发现。它定义了工具列表、schema、调用结果等约定，让不同客户端更容易理解和调用工具。当然生产环境也可以把 MCP 和 HTTP 服务结合起来。

## JSON-RPC/stdin/stdout

### 为什么 stdout 不能写日志？

stdio transport 下 stdout 是 JSON-RPC 协议流。客户端会把 stdout 当成协议消息解析，如果日志写到 stdout，就会污染协议流。这个项目把日志重定向到 stderr，就是为了保证协议输出干净。

### MCP 初始化流程是什么？

典型流程是 `initialize`，然后客户端发 `notifications/initialized`，接着可以调用 `tools/list` 获取工具，再用 `tools/call` 调用工具。项目的 e2e 测试里模拟了这个流程。

## Tool schema 设计

### `query_knowledge_hub` 的 schema 有哪些关键点？

它要求 `query` 必填，`top_k` 可选且限制 1 到 20，`collection` 用于限定知识范围。这个设计既让 Agent 容易调用，又能控制上下文规模和检索范围。

### description 重要吗？

重要。模型选择工具时会参考工具描述和参数描述。如果 description 模糊，模型就可能在错误场景调用工具，或者填错参数。

## RAG tool 如何服务 Agent

### Agent 为什么需要 RAG tool？

Agent 自身没有项目文档或企业知识的最新事实。RAG tool 可以把外部知识按需取回，让 Agent 基于证据回答，而不是凭模型记忆生成。

### Agent 什么时候应该二次检索？

当第一次结果不够相关、collection 可能选错、用户问题包含多个子问题，或者结果缺少关键实体时，可以改写 query 或调整 collection 做二次检索。

## 错误处理与降级

### 工具失败应该怎么返回？

不应该直接抛堆栈给 Agent。应该返回简洁、可理解、可恢复的错误。这个项目的 `ProtocolHandler` 会捕获参数错误和内部错误，并用 `CallToolResult(isError=True)` 返回。

### 如果 `query_knowledge_hub` 没有查到结果怎么办？

Agent 可以先告诉用户检索结果不足，然后尝试换 query、调用 `list_collections` 检查 collection，或者建议用户先摄取文档。不要硬编答案。

## 安全和权限边界

### Agent 工具为什么需要权限分级？

因为不同工具风险不同。查询类工具通常是只读的，摄取、删除、执行命令类工具会改变系统状态，应该要求更严格的权限、确认和审计。

### 当前项目有哪些边界设计？

已有边界包括 `top_k` 最大值、collection 作用域、工具错误不泄漏堆栈。未来还可以加入 collection allowlist、路径限制、敏感 metadata 过滤和工具权限分级。

## 可观测性和调试

### Agent 工具调用为什么需要 trace？

当 Agent 回答错了，问题可能出在工具没调、参数错、检索结果差、结果太多、或者模型没有正确使用工具结果。trace 可以记录工具调用参数、耗时、结果摘要和错误，帮助定位。

### 这个项目有哪些可观测基础？

项目已有日志、TraceContext、Dashboard 和查询/摄取 trace。下一步可以把 MCP tool call 本身也纳入 trace。

## 与 LangChain/传统函数调用的区别

### MCP 和 LangChain tools 是什么关系？

LangChain tools 更像某个框架内部的工具抽象。MCP 是一个跨客户端、跨工具服务的协议。MCP tool 可以被不同 MCP client 调用，不局限在一个 Agent 框架里。

## 如何继续 Agent 化

### 如果让你继续改造这个项目，你会做什么？

我会优先做三件事：第一，补充只读和写入工具的权限分级；第二，增加 tool call trace 和结构化错误码；第三，写一个 demo agent client，演示 `list_collections -> query_knowledge_hub -> get_document_summary -> final answer` 的多步流程。

