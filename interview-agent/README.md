# Agent/MCP 工具工程面试准备手册

这个目录用于把当前 `modular-rag-mcp-server` 项目从“RAG 项目”进一步整理成“Agent 可调用的知识工具服务”来准备面试。重点不是再讲一遍向量检索，而是讲清楚模型或 Agent 如何通过 MCP 安全、稳定、可观察地调用工具。

推荐阅读顺序：

1. `01_agent_role_positioning.md`：理解 Agent 开发工程师需要什么能力，以及这个项目怎么重新包装。
2. `02_mcp_server_deep_dive.md`：精读 MCP Server、stdio、JSON-RPC 生命周期和协议处理。
3. `03_tool_design_and_schema.md`：拆解 3 个 MCP tools 的 schema、用途和边界。
4. `04_agent_workflow_with_rag_tools.md`：设计 Agent 如何组合这些 RAG tools 完成多步任务。
5. `05_interview_questions_and_answers.md`：准备 Agent/MCP 面试问答。
6. `06_next_steps_to_agentize_project.md`：整理下一步把项目继续 Agent 化的路线。
7. `07_demo_and_debug_playbook.md`：准备面试 Demo 和 Debug 话术。
8. `08_7_day_agent_study_plan.md`：按 7 天节奏推进。

和 RAG 面试材料的区别：

- RAG 方向重点讲召回质量、chunk、embedding、向量库、BM25、RRF、rerank。
- Agent/MCP 方向重点讲工具接口、协议生命周期、schema 设计、工具选择、上下文返回、错误处理、安全边界和可观测性。

这个项目还不是完整的 Agent loop。它没有自己实现 planner、memory、multi-step reasoning，但它已经具备 Agent 很需要的一层：把知识库能力包装成 MCP tools，让外部 Agent 或客户端可以发现工具、理解参数、调用工具、拿到结果。

