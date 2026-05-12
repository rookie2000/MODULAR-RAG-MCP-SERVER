# 摄取 Pipeline 深入理解

## 入口脚本

主入口是 `scripts/ingest.py`。它负责命令行参数、配置加载、文件发现、pipeline 初始化、逐文件处理和结果汇总。

常用命令：

```powershell
uv run python scripts/ingest.py --path tests/fixtures/sample_documents/simple.pdf --collection demo
```

目录预览：

```powershell
uv run python scripts/ingest.py --path tests/fixtures/sample_documents --dry-run
```

## 参数解释

- `--path` / `-p`：必填。可以是单个 PDF，也可以是目录。目录会递归查找 `.pdf` 和 `.PDF`。
- `--collection` / `-c`：集合名称，默认是 `default`。摄取和查询必须使用同一个 collection 才容易查到。
- `--force` / `-f`：强制重新处理。默认会根据文件 hash 跳过已处理文件。
- `--config`：配置文件路径，默认是 `config/settings.yaml`。
- `--verbose` / `-v`：打开更详细日志，适合调试失败文件。
- `--dry-run`：只列出将处理的文件，不执行摄取。

`--path` 不传会报错，因为 `argparse` 中设置了 `required=True`。

## Pipeline 六阶段

核心实现是 `src/ingestion/pipeline.py` 的 `IngestionPipeline.run()`。

### 1. File Integrity Check

系统对文件计算 SHA256 hash，并记录到 `data/db/ingestion_history.db`。如果文件之前成功处理过，且没有使用 `--force`，就会跳过。

面试可讲点：这是幂等性设计，避免重复 embedding、重复写向量库，也能节省 token 和时间。

### 2. Document Loading

`PdfLoader` 读取 PDF，提取文本和图片。图片会保存到 `data/images/<collection>/` 相关目录，后续可注册到图片索引。

面试可讲点：RAG 的输入经常是 PDF、Office、网页等非结构化数据，loader 是把原始文件转成统一 Document 对象的边界。

### 3. Document Chunking

`DocumentChunker` 根据 `config/settings.yaml` 中的配置切分文本：

```yaml
ingestion:
  chunk_size: 1000
  chunk_overlap: 200
  splitter: "recursive"
```

`chunk_size` 太大，召回粒度粗，可能带入无关内容；太小，语义不完整，chunk 数量增加，embedding 成本也增加。`chunk_overlap` 用于保留上下文连续性，但 overlap 太大会造成重复内容和存储膨胀。

### 4. Transform Pipeline

包含三类增强：

- `ChunkRefiner`：可用 LLM 优化 chunk 文本。
- `MetadataEnricher`：可用 LLM 或规则生成 title、summary、tags。
- `ImageCaptioner`：在 `vision_llm.enabled=true` 时给图片生成描述。

当前默认配置里：

```yaml
chunk_refiner:
  use_llm: true

metadata_enricher:
  use_llm: true
```

面试可讲点：这些增强可能提升检索和展示效果，但会明显增加延迟和 token 成本。生产环境中通常要根据文档规模、预算和效果评估来决定是否开启。

### 5. Encoding

`BatchProcessor` 同时处理：

- Dense encoding：调用 embedding provider 生成向量。
- Sparse encoding：生成 BM25 所需的词频、文档长度等统计。

当前配置中 embedding provider 是 `minimax`：

```yaml
embedding:
  provider: "minimax"
  model: "embo-01"
```

面试可讲点：embedding 不是聊天式对话，通常只按输入文本生成向量，但仍然会产生 API 成本和网络延迟。

### 6. Storage

写入三类存储：

- Chroma：保存 dense vector 和 chunk metadata。
- BM25：保存 sparse 索引，用于关键词检索。
- ImageStorage：保存图片索引信息。

面试可讲点：一个 RAG 系统往往不是只有向量库。为了提升召回质量，常常需要向量索引、关键词索引、原文/metadata 存储、trace 存储等多种数据结构。

## 为什么处理目录会慢

目录摄取不是“第二步”，而是批量处理示例。`tests/fixtures/sample_documents` 里有多个 PDF，系统会逐个处理。

慢的原因通常是：

- 多个 PDF，而不是一个 `simple.pdf`。
- 长文档会切出更多 chunk。
- `chunk_refiner.use_llm=true` 会对 chunk 调 LLM。
- `metadata_enricher.use_llm=true` 会继续调 LLM。
- embedding provider 需要访问外部 API。
- Chroma、BM25、图片索引都需要持久化写入。
- 第一次运行 `uv run` 可能有环境启动开销。

## 面试回答模板

### 你们如何避免重复摄取？

我会先讲这个项目里的实现：摄取前会对文件计算 SHA256 hash，并在 SQLite 的 ingestion history 里记录处理状态。如果同一个文件已经成功处理过，默认会 skip。只有用户传 `--force` 时才会重新处理。这样可以保证摄取幂等，避免重复 embedding 和重复写索引。

### 为什么要同时存 Chroma 和 BM25？

因为 Dense 和 Sparse 解决的问题不同。Chroma 里的 dense vector 适合语义相似召回，比如用户换一种说法提问；BM25 适合关键词、专有名词、数字、配置项这类精确匹配。生产 RAG 里只靠向量检索容易漏掉关键词强相关内容，只靠 BM25 又不理解语义，所以混合检索更稳。

### chunk_size 怎么选？

我会根据文档类型、模型上下文、查询粒度和评估结果来选。`chunk_size` 大一点可以保留上下文，但召回结果可能不够聚焦；小一点更精确，但容易切断语义，也会增加 chunk 数、embedding 成本和索引规模。这个项目默认 `1000`，`overlap=200`，适合作为起点，然后通过 hit rate、MRR、人工检查 top results 来调。

