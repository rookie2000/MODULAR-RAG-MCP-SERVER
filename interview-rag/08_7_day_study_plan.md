# 7 天冲刺计划

## Day 1：跑通主流程

目标：知道项目能做什么，跑通摄取、查询和 Dashboard。

阅读文件：

- `README.md`
- `teach-codex.md`
- `docs/environment.md`
- `config/settings.yaml`

运行命令：

```powershell
uv run python scripts/ingest.py --path tests/fixtures/sample_documents --dry-run
uv run python scripts/ingest.py --path tests/fixtures/sample_documents/simple.pdf --collection demo
uv run python scripts/query.py --query "这个文档讲了什么" --collection demo --verbose
uv run python scripts/start_dashboard.py --port 8501
```

产出物：

- 记录每条命令的作用。
- 记录一次成功查询的输出。
- 记录遇到的报错和解决方式。

验收标准：

- 能解释 `uv run`、`--path`、`--collection`、`--verbose`。
- 能说清楚为什么要先跑 `simple.pdf`。

## Day 2：精读摄取链路

目标：理解文件如何进入知识库。

阅读文件：

- `scripts/ingest.py`
- `src/ingestion/pipeline.py`
- `src/libs/loader/pdf_loader.py`
- `src/ingestion/chunking/document_chunker.py`

运行命令：

```powershell
uv run python scripts/ingest.py --path tests/fixtures/sample_documents/simple.pdf --collection demo --force --verbose
```

产出物：

- 画出摄取六阶段。
- 写出 `--force` 和 hash 去重的关系。
- 总结目录摄取慢的原因。

验收标准：

- 能回答“如何避免重复摄取”。
- 能回答“chunk_size 怎么选”。

## Day 3：精读查询和 RRF

目标：理解问题如何被检索和排序。

阅读文件：

- `scripts/query.py`
- `src/core/query_engine/hybrid_search.py`
- `src/core/query_engine/fusion.py`
- `src/core/query_engine/dense_retriever.py`
- `src/core/query_engine/sparse_retriever.py`

运行命令：

```powershell
uv run python scripts/query.py --query "RRF 是什么" --collection demo --verbose
uv run python scripts/query.py --query "这个项目如何做混合检索" --collection demo --verbose
```

产出物：

- 解释 Dense、Sparse、RRF 的区别。
- 写出 RRF 公式和为什么不用直接加分。

验收标准：

- 能回答“为什么要混合检索”。
- 能回答“RRF 解决什么问题”。

## Day 4：做配置实验

目标：理解参数如何影响流程、成本和结果。

阅读文件：

- `config/settings.yaml`
- `interview/04_config_experiments.md`

实验：

- 关闭 `chunk_refiner.use_llm` 和 `metadata_enricher.use_llm`。
- 调整 `chunk_size` 和 `chunk_overlap`。
- 调整 `dense_top_k`、`sparse_top_k`、`fusion_top_k`。
- 对比 `rerank.enabled` 开关。

产出物：

- 每个实验记录修改点、命令、观察现象、面试结论。

验收标准：

- 能把参数变化和成本、延迟、召回质量联系起来。

## Day 5：读 MCP、Dashboard、Trace

目标：理解项目如何从脚本变成可接入的服务能力。

阅读文件：

- `src/mcp_server/tools/query_knowledge_hub.py`
- `src/mcp_server/protocol_handler.py`
- `src/core/trace/`
- `src/observability/dashboard/`

运行命令：

```powershell
uv run python scripts/start_dashboard.py --port 8501
```

产出物：

- 记录 MCP tool 输入参数。
- 记录 Dashboard 能看到哪些页面。
- 解释 Trace 对 RAG 调试的价值。

验收标准：

- 能回答“MCP 在项目里起什么作用”。
- 能回答“为什么 RAG 项目需要 Trace”。

## Day 6：准备面试话术和问答

目标：把源码理解转化成面试表达。

阅读文件：

- `interview/01_project_understanding.md`
- `interview/05_interview_questions_and_answers.md`
- `interview/06_project_story_resume_pitch.md`

产出物：

- 背熟 1 分钟项目介绍。
- 准备 3 个最能体现工程能力的亮点。
- 准备 3 个诚实边界和改进计划。

验收标准：

- 能自然讲出项目，不像背 README。
- 能诚实说明项目不是从零原创，但能讲清接手、验证和理解过程。

## Day 7：模拟面试和复盘

目标：把材料转成稳定输出能力。

模拟问题：

- 这个项目整体架构是什么？
- 摄取一篇 PDF 发生了什么？
- 为什么要 Dense + Sparse？
- RRF 是什么？
- rerank 有什么代价？
- 怎么评估 RAG 效果？
- 如果让你继续优化，你会做什么？

产出物：

- 一版最终简历项目描述。
- 一份个人薄弱点清单。
- 一份面试现场 Demo 流程。

验收标准：

- 5 分钟能讲完整项目。
- 10 分钟能深入讲摄取和查询两条链路。
- 遇到不会的问题能回到工程取舍，而不是硬编。

