# RAG 应用工程面试准备手册

这个目录把当前 `modular-rag-mcp-server` 项目整理成一套面向 AI 大模型应用岗位，尤其是 RAG 应用工程方向的面试材料。目标不是背概念，而是能拿着这个项目讲清楚：系统解决什么问题、链路怎么跑、参数怎么影响结果、工程上做了哪些取舍。

推荐阅读顺序：

1. `01_project_understanding.md`：先建立项目全局地图，准备 1/3/5 分钟项目介绍。
2. `02_ingestion_pipeline_deep_dive.md`：理解文档如何进入知识库。
3. `03_query_retrieval_deep_dive.md`：理解问题如何被检索、融合、返回。
4. `04_config_experiments.md`：通过改参数观察系统行为。
5. `05_interview_questions_and_answers.md`：按模块准备面试问答。
6. `06_project_story_resume_pitch.md`：整理简历和面试表达。
7. `07_debug_and_demo_playbook.md`：准备现场演示和 Debug。
8. `08_7_day_study_plan.md`：按 7 天节奏推进。

你最终要达到的状态：

- 能讲架构：MCP Server、Ingestion、Query Engine、Storage、Observability、Evaluation 的边界。
- 能讲 RAG 流程：PDF 到 chunk，再到 embedding、Chroma、BM25、查询、RRF、rerank。
- 能解释参数：`chunk_size`、`chunk_overlap`、`dense_top_k`、`sparse_top_k`、`fusion_top_k`、`rrf_k`、`rerank.enabled`。
- 能回答工程取舍：为什么混合检索、为什么需要 trace、为什么目录摄取慢、如何控制成本、如何扩展 provider。
- 能诚实表达：这是接手学习的项目，但你已经通过源码阅读、运行验证和参数实验建立了自己的理解。

