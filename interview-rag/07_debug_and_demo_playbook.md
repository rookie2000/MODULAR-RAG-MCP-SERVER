# Debug 与 Demo 手册

## VS Code Debug 参数配置

`scripts/ingest.py` 使用 `argparse`，其中 `--path` 是必填参数。不传参数 Debug 会触发参数错误并退出。

可以在 `.vscode/launch.json` 中加入：

```json
{
    "name": "Debug ingest simple.pdf",
    "type": "debugpy",
    "request": "launch",
    "program": "${workspaceFolder}/scripts/ingest.py",
    "cwd": "${workspaceFolder}",
    "args": [
        "--path",
        "tests/fixtures/sample_documents/simple.pdf",
        "--collection",
        "demo",
        "--verbose"
    ],
    "console": "integratedTerminal"
}
```

只想预览目录时：

```json
"args": [
    "--path",
    "tests/fixtures/sample_documents",
    "--dry-run"
]
```

## Demo 命令顺序

### 1. 预览目录

```powershell
uv run python scripts/ingest.py --path tests/fixtures/sample_documents --dry-run
```

讲解点：目录模式会递归发现 PDF，dry-run 不会真正摄取，适合先确认处理范围。

### 2. 摄取单个 PDF

```powershell
uv run python scripts/ingest.py --path tests/fixtures/sample_documents/simple.pdf --collection demo
```

讲解点：先用最小 PDF 跑通链路，避免一上来处理整个目录导致等待太久。

### 3. 查询

```powershell
uv run python scripts/query.py --query "这个文档讲了什么" --collection demo --verbose
```

讲解点：`--verbose` 能看到 Dense、Sparse、Fusion 等中间结果，适合展示混合检索。

### 4. 启动 Dashboard

```powershell
uv run python scripts/start_dashboard.py --port 8501
```

讲解点：Dashboard 用于观察数据、摄取记录、查询 trace 和评估面板。

## 面试现场 5-8 分钟演示路线

1. 用 30 秒介绍项目定位：模块化 RAG MCP Server。
2. 用 1 分钟展示 `config/settings.yaml`：provider、chunk、retrieval、rerank。
3. 用 1 分钟运行或展示 `--dry-run`：说明文件发现和安全预检。
4. 用 1-2 分钟讲 `ingest.py -> IngestionPipeline` 六阶段。
5. 用 1-2 分钟运行 query 或展示输出：讲 Dense + Sparse + RRF。
6. 用 1 分钟讲 MCP tool 和 Dashboard：说明工程化和可观测性。
7. 最后讲改进计划：评估报告、索引一致性、生产化部署。

## 常见问题和处理

### 缺少 `--path`

现象：Debug 或命令行直接运行 `scripts/ingest.py` 报参数错误。

原因：`--path` 是必填参数。

处理：

```powershell
uv run python scripts/ingest.py --path tests/fixtures/sample_documents/simple.pdf --collection demo
```

### API key 缺失

现象：初始化 LLM 或 embedding provider 失败。

原因：`config/settings.yaml` 或环境变量中没有配置 provider 所需密钥。

处理：检查 `config/test_credentials.yaml.example`，不要把真实 key 提交到仓库。调试时可以先关闭 LLM 增强，减少外部调用。

### 重复摄取被 skip

现象：日志显示文件已处理，跳过。

原因：文件 hash 已存在于 ingestion history。

处理：

```powershell
uv run python scripts/ingest.py --path tests/fixtures/sample_documents/simple.pdf --collection demo --force
```

### collection 不一致导致查不到

现象：摄取成功，但 query 没有相关结果。

原因：摄取时用了 `--collection demo`，查询时用了其他 collection。

处理：

```powershell
uv run python scripts/query.py --query "这个文档讲了什么" --collection demo --verbose
```

### 目录摄取太慢

原因：多个 PDF、多 chunk、LLM refine、metadata enrich、embedding API、持久化写入。

处理：先用 `simple.pdf`，或者关闭 LLM 增强后再做参数实验。

