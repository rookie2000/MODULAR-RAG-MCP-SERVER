# 项目故事、简历表达与面试话术

## 简历项目描述

项目名称：模块化 RAG MCP 知识库服务

简历 bullet 示例：

- 基于 Python 构建模块化 RAG 知识库服务，支持 PDF 摄取、文本切块、Embedding、Chroma 向量存储、BM25 稀疏索引和混合检索。
- 设计并理解 Dense + Sparse + RRF 的检索链路，结合语义召回和关键词召回提升技术文档场景下的检索覆盖率。
- 通过配置驱动方式支持 OpenAI、Azure、Ollama、MiniMax 等 LLM/Embedding provider，便于不同模型服务切换。
- 通过 MCP tools 将知识库查询能力暴露给外部客户端，并结合 Trace、Dashboard、Evaluation 支持调试和效果验证。
- 对 ingestion 参数、chunk 策略、top_k、rerank 等进行实验分析，总结召回质量、延迟和 token 成本之间的取舍。

## 面试开场介绍

我最近重点准备了一个模块化 RAG MCP Server 项目。它的核心是把 PDF 文档离线摄取成知识库，在线通过 Dense + Sparse 混合检索和 RRF 融合找到相关 chunk，再通过 MCP tool 暴露给外部客户端。这个项目比较适合作为 RAG 应用工程项目来讲，因为它不只是调用一次大模型，而是覆盖了摄取、检索、排序、存储、配置、可观测性和评估这些工程环节。

## 如何诚实表达“这是别人做的项目”

推荐表达：

这个项目不是我从零开始写的，我是以接手和二次理解的方式准备的。我做的事情是先跑通主流程，然后沿着 `ingest.py`、`pipeline.py`、`query_engine` 和 MCP tools 去读源码，整理了摄取链路、查询链路和参数实验。我更关注的是能否把一个已有 RAG 工程快速理解、验证、调参和讲清楚，这也是实际工作中经常遇到的场景。

避免表达：

- “这个项目全部是我写的。”
- “我只是跑了一下，不太清楚。”
- “代码里应该是这样。”

更好的表达是：

- “已有项目里是这样实现的，我通过运行和源码阅读验证了这一点。”
- “这部分如果让我继续做，我会从评估和索引一致性入手改进。”
- “我能讲清楚它的链路和取舍，但不会把不是我做的工作包装成原创。”

## 可讲亮点

### 模块化 provider

LLM、Embedding、Vector Store、Reranker 等能力通过 base class 和 factory 管理。面试时可以强调这降低了供应商绑定，方便在 OpenAI、Azure、Ollama、MiniMax 之间切换。

### 混合检索

Dense 解决语义相关，BM25 解决关键词精确匹配，RRF 解决异构分数融合。这个亮点非常适合 RAG 应用岗位。

### Trace 和 Dashboard

RAG 调试不能只看最终答案。Trace 能看到 load、split、transform、embed、upsert、search、fusion 等中间结果，Dashboard 则提升可观察性。

### Evaluation

项目有 golden test set 和 evaluator 结构。可以讲：RAG 参数调优不能只凭感觉，需要用 hit rate、MRR 等指标做回归。

### MCP 接入

MCP tool 把知识库能力变成标准工具，使它能被外部 Agent 或客户端调用。这让项目不只是本地脚本，而是能嵌入大模型应用生态。

## 诚实边界

已有能力：

- 摄取 pipeline
- Chroma 和 BM25 存储
- Dense + Sparse + RRF
- MCP tools
- Dashboard
- Evaluation 框架
- Provider 工厂结构

我通过学习和实验掌握的能力：

- 跑通 ingest/query/dashboard
- 理解参数和链路
- 分析目录摄取慢的原因
- 准备调参实验
- 能解释面试中的工程取舍

可以计划优化的能力：

- 增加系统化评估报告
- 增加批量摄取进度和失败重试
- 改进索引删除和更新一致性
- 增加生产部署、鉴权、限流、监控

