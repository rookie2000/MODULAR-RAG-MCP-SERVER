# Agent 开发工程师定位

## Agent 岗位常见能力模型

Agent 开发工程师不只是“会调大模型接口”。更重要的是把模型放进一个能做事的系统里：

- Tool calling：把外部能力封装成模型可调用的工具。
- MCP：用标准协议把工具暴露给不同客户端。
- 上下文工程：控制给模型的工具结果数量、结构、引用和摘要。
- 工具边界：明确工具能做什么、不能做什么、参数如何约束。
- 错误恢复：工具失败时返回可理解错误，而不是让 Agent 直接看到堆栈。
- 权限与安全：区分只读、写入、危险操作，限制路径、collection、top_k 等。
- 可观测性：记录 tool call、参数、耗时、错误、结果摘要，方便调试。

## 用当前项目重新包装

从 RAG 视角看，这个项目是知识库系统。从 Agent 视角看，它是一个 MCP 工具服务：

```text
Agent / MCP Client
  -> initialize
  -> tools/list
  -> tools/call
  -> query_knowledge_hub / list_collections / get_document_summary
  -> RAG 检索和数据访问
  -> 返回可引用上下文
```

它当前没有实现完整 Agent loop，但已经完成了 Agent 应用里非常关键的一层：工具化能力。面试时可以说：我把它理解为一个可供 Agent 使用的知识工具服务器，重点研究了 MCP stdio、JSON-RPC 生命周期、tool schema、工具注册、错误处理和下一步 Agent 化改造。

## 1 分钟介绍

这个项目原本是一个模块化 RAG MCP Server。我从 Agent 开发工程师角度重新理解它：它把知识库查询能力封装成 MCP tools，外部 Agent 可以通过 `tools/list` 发现工具，再通过 `tools/call` 调用 `query_knowledge_hub`、`list_collections`、`get_document_summary`。我重点关注的是工具 schema 设计、stdio 协议、JSON-RPC 生命周期、错误边界和如何让 RAG 能力成为 Agent 的可靠工具。

## 3 分钟介绍

这个项目的 Agent 价值在 MCP 层。服务通过 `src/mcp_server/server.py` 以 stdio transport 启动，stdout 只输出 JSON-RPC 协议消息，日志统一转到 stderr，避免污染协议流。`protocol_handler.py` 负责工具注册、schema 暴露和工具执行，默认注册了三个工具：查询知识库、列出 collection、获取文档摘要。

从 Agent 的使用流程看，模型可以先调用 `list_collections` 判断有哪些知识集合，再用 `query_knowledge_hub` 检索相关内容，必要时用 `get_document_summary` 查看文档级摘要。RAG 负责提供知识，Agent 负责决定何时调用工具、是否二次查询、如何组织最终回答。

我会把这个项目讲成一个“Agent 可调用的知识服务”，重点不是模型自己规划，而是工具层如何做得可发现、可约束、可调试。

## 5 分钟介绍

Agent 应用落地时，真正困难的部分经常不只是 prompt，而是工具如何被模型稳定调用。这个项目提供了一个很好的切入点：它把 RAG 知识库能力通过 MCP 暴露出去，形成一个标准工具服务。

服务入口是 `src/mcp_server/server.py`，使用官方 MCP SDK 的 stdio transport。这里有一个很重要的工程细节：stdout 必须只保留 JSON-RPC 消息，因为 MCP client 会把 stdout 当协议流读取。如果普通日志写到 stdout，就会破坏协议解析，所以项目专门把日志重定向到 stderr。它还提前 preload Chroma 和内部查询模块，避免 worker thread 中 lazy import 触发 import lock 问题。

工具协议层在 `src/mcp_server/protocol_handler.py`。它维护一个工具注册表，每个工具包含 name、description、input_schema 和 handler。MCP client 调 `tools/list` 时返回 schema，调 `tools/call` 时根据工具名执行 handler，并把返回值统一包装成 `CallToolResult`。参数错误和内部异常会被捕获，避免直接泄漏堆栈。

工具设计上，当前有三个默认工具。`list_collections` 用于发现可用知识集合；`query_knowledge_hub` 用于混合检索知识库；`get_document_summary` 用于查看文档摘要和 metadata。这样的工具组合可以支持一个 Agent 做“先发现数据范围，再检索，再补充文档上下文，最后综合回答”的工作流。

如果继续改造，我会补充写入类工具、权限分级、结构化错误码、tool call trace 和一个 demo agent client。这样这个项目就能从“可被 Agent 调用的 RAG 工具服务”进一步走向“可演示的 Agent 应用”。

