# 参数实验手册

这些实验都建议手动修改 `config/settings.yaml` 后运行命令观察。不要提交真实 API key，也不要把实验配置当成永久最佳配置。

每次实验建议记录：

- 修改了什么参数。
- 摄取耗时、chunk 数、是否调用 LLM。
- 查询 top results 是否更相关。
- 是否出现 skip、报错或 collection 不一致。
- 面试中能总结出什么工程结论。

## 实验 1：关闭 LLM 增强，观察速度和 token 成本

目的：理解摄取慢和 token 成本的来源。

修改点：

```yaml
ingestion:
  chunk_refiner:
    use_llm: false

  metadata_enricher:
    use_llm: false
```

运行：

```powershell
uv run python scripts/ingest.py --path tests/fixtures/sample_documents/simple.pdf --collection demo_no_llm --force
```

观察指标：

- 是否明显更快。
- 日志中 LLM refined / enriched 数量是否减少。
- 生成 chunk 的 title、summary、tags 是否变弱。

面试可讲结论：LLM 增强不是 RAG 必需环节，它是效果和成本之间的取舍。小规模、高价值文档可以开启；大规模批处理时要谨慎。

## 实验 2：调整 chunk_size 和 chunk_overlap

目的：理解 chunk 粒度对召回和成本的影响。

修改点 A：

```yaml
ingestion:
  chunk_size: 500
  chunk_overlap: 100
```

修改点 B：

```yaml
ingestion:
  chunk_size: 1500
  chunk_overlap: 200
```

运行：

```powershell
uv run python scripts/ingest.py --path tests/fixtures/sample_documents/chinese_technical_doc.pdf --collection chunk_exp --force
uv run python scripts/query.py --query "RRF 是什么" --collection chunk_exp --verbose
```

观察指标：

- chunk 数量变化。
- 单个结果是否更聚焦。
- 查询结果是否缺上下文。
- embedding 调用数量是否增加。

面试可讲结论：chunk 参数不是固定答案，要根据文档结构、问题类型、模型上下文和评估指标调优。

## 实验 3：调整 dense_top_k、sparse_top_k、fusion_top_k

目的：理解召回候选数量和最终结果数量的关系。

修改点：

```yaml
retrieval:
  dense_top_k: 5
  sparse_top_k: 5
  fusion_top_k: 5
  rrf_k: 60
```

对比：

```yaml
retrieval:
  dense_top_k: 30
  sparse_top_k: 30
  fusion_top_k: 10
  rrf_k: 60
```

运行：

```powershell
uv run python scripts/query.py --query "这个项目如何做混合检索" --collection demo --verbose
```

观察指标：

- Dense、Sparse、Fusion 中间结果数量。
- top results 是否更稳定。
- 响应时间是否变化。

面试可讲结论：召回 top_k 大一些可以提高覆盖，但不是越大越好，会带来排序、rerank 和响应时间成本。

## 实验 4：调整 rrf_k

目的：理解 RRF 平滑参数对排序的影响。

修改点：

```yaml
retrieval:
  rrf_k: 20
```

对比：

```yaml
retrieval:
  rrf_k: 100
```

运行：

```powershell
uv run python scripts/query.py --query "embedding provider 怎么配置" --collection demo --verbose
```

观察指标：

- 同一个文档如果在 dense 和 sparse 都靠前，是否排名更高。
- 只在单一路径出现的文档是否还能进入结果。

面试可讲结论：RRF 的 `k` 控制 rank contribution 的平滑程度。实际调参要看验证集和人工检查结果。

## 实验 5：开启或关闭 rerank

目的：理解召回和精排的分工。

修改点：

```yaml
rerank:
  enabled: true
  provider: "llm"
  top_k: 5
```

或保持默认：

```yaml
rerank:
  enabled: false
  provider: "none"
```

运行：

```powershell
uv run python scripts/query.py --query "如何避免重复摄取" --collection demo --verbose
uv run python scripts/query.py --query "如何避免重复摄取" --collection demo --no-rerank
```

观察指标：

- top results 排序是否变化。
- 响应时间是否增加。
- 是否产生额外 LLM 成本。

面试可讲结论：rerank 适合提升最终排序，但要控制候选数量，并通过评估确认收益大于成本。

## 实验 6：dry-run、force 和 collection

目的：理解命令行参数对系统行为的影响。

预览目录：

```powershell
uv run python scripts/ingest.py --path tests/fixtures/sample_documents --dry-run
```

强制重跑：

```powershell
uv run python scripts/ingest.py --path tests/fixtures/sample_documents/simple.pdf --collection demo --force
```

不同 collection：

```powershell
uv run python scripts/ingest.py --path tests/fixtures/sample_documents/simple.pdf --collection demo_a
uv run python scripts/query.py --query "这个文档讲了什么" --collection demo_b --verbose
```

观察指标：

- `--dry-run` 是否只列文件。
- 不加 `--force` 是否 skip 已处理文件。
- collection 不一致时是否查不到预期结果。

面试可讲结论：collection 是命名空间，force 是重处理开关，dry-run 是安全预检能力。这些都是工程化脚本常见但重要的细节。

