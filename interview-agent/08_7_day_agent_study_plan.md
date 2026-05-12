# 7 天 Agent 方向冲刺计划

## Day 1：理解 Agent 岗位和 MCP 基础

目标：把项目从 RAG 视角切换到 Agent 工具服务视角。

阅读文件：

- `interview-agent/README.md`
- `interview-agent/01_agent_role_positioning.md`
- `README.md`
- `teach-codex.md`

产出物：

- 写出 1 分钟 Agent 方向项目介绍。
- 列出 Agent 工程师需要的 6 个能力点。

验收标准：

- 能说清“这个项目不是完整 Agent loop，但有 MCP 工具层”。

## Day 2：精读 MCP server 和 protocol handler

目标：理解 stdio、JSON-RPC 和工具注册。

阅读文件：

- `src/mcp_server/server.py`
- `src/mcp_server/protocol_handler.py`
- `interview-agent/02_mcp_server_deep_dive.md`

产出物：

- 画出 initialize、tools/list、tools/call 流程。
- 总结 stdout/stderr 分离原因。
- 总结 `_preload_heavy_imports()` 的工程价值。

验收标准：

- 能回答“为什么 MCP stdio 不能把日志写 stdout”。
- 能回答“ProtocolHandler 如何执行工具”。

## Day 3：精读 3 个 tools

目标：理解 tool schema 和工具边界。

阅读文件：

- `src/mcp_server/tools/query_knowledge_hub.py`
- `src/mcp_server/tools/list_collections.py`
- `src/mcp_server/tools/get_document_summary.py`
- `interview-agent/03_tool_design_and_schema.md`

产出物：

- 为每个工具写出用途、参数、失败场景、Agent 使用时机。

验收标准：

- 能回答“什么是好的 tool schema”。
- 能回答“为什么 top_k 要有限制”。

## Day 4：跑 MCP client 测试

目标：从测试理解 wire-level 生命周期。

阅读文件：

- `tests/e2e/test_mcp_client.py`
- `tests/integration/test_mcp_server.py`

运行命令：

```powershell
uv run pytest tests/e2e/test_mcp_client.py -v
uv run pytest tests/integration/test_mcp_server.py -v
```

产出物：

- 记录 initialize、tools/list、tools/call 的请求形态。
- 记录测试验证了哪些协议约束。

验收标准：

- 能说清 e2e 测试和普通单元测试的区别。

## Day 5：设计 Agent 使用 RAG tools 的工作流

目标：能讲出 Agent 如何组合工具，而不是只会单次 query。

阅读文件：

- `interview-agent/04_agent_workflow_with_rag_tools.md`
- `src/core/response/response_builder.py`
- `src/core/trace/`

产出物：

- 设计一个 `list_collections -> query -> summary -> final answer` 的流程。
- 总结上下文工程注意点。

验收标准：

- 能回答“Agent 和普通 RAG query 的区别是什么”。

## Day 6：准备 Agent/MCP 面试问答

目标：把源码理解转成面试表达。

阅读文件：

- `interview-agent/05_interview_questions_and_answers.md`
- `interview-agent/06_next_steps_to_agentize_project.md`

产出物：

- 背熟 10 个高频问题。
- 准备 3 个下一步改造点：权限、结构化错误、tool trace。

验收标准：

- 能自然回答 MCP、tool schema、错误边界、安全权限相关问题。

## Day 7：模拟面试和复盘

目标：形成稳定输出。

模拟问题：

- 这个项目和 Agent 开发有什么关系？
- MCP stdio 为什么要保持 stdout 干净？
- tools/list 和 tools/call 分别做什么？
- 如何设计一个模型容易调用的 tool？
- `query_knowledge_hub` 的边界在哪里？
- 如果工具失败，Agent 应该怎么恢复？
- 如何继续把这个项目 Agent 化？

产出物：

- 一版 Agent 方向简历项目描述。
- 一份 5-8 分钟 Demo 讲稿。
- 一份薄弱点清单。

验收标准：

- 5 分钟讲清项目的 Agent/MCP 价值。
- 10 分钟深入讲协议层、工具层和下一步改造。

