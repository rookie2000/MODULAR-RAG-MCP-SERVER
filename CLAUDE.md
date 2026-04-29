# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Modular RAG MCP Server** - a pluggable Retrieval-Augmented Generation framework that exposes tools via the Model Context Protocol (MCP). It's designed for AI assistants (Copilot, Claude Desktop) to query private knowledge bases.

## Common Commands

### Setup & Installation
```bash
pip install -e .
```

### Run Tests
```bash
# All tests
pytest

# Single test file
pytest tests/unit/test_llm_factory.py

# Specific test
pytest tests/unit/test_llm_factory.py::test_factory_creates_correct_provider -v
```

### Run the Server
```bash
# As MCP Server (stdio mode)
python -m src.mcp_server.server
```

### Run Dashboard
```bash
streamlit run src/observability/dashboard/app.py
```

### Ingest Documents
```bash
python -c "from src.ingestion.pipeline import IngestionPipeline; IngestionPipeline().run('path/to/doc.pdf')"
```

## Architecture

### Core Layers

| Layer | Purpose |
|-------|---------|
| **MCP Server** (`src/mcp_server/`) | Exposes tools via MCP protocol (query_knowledge_hub, list_collections, get_document_summary) |
| **Ingestion** (`src/ingestion/`) | PDF → Markdown → Chunk → Transform → Embedding → Upsert pipeline |
| **Query Engine** (`src/core/query_engine/`) | Hybrid Search (BM25 + Dense) + RRF Fusion + Rerank |
| **Response** (`src/core/response/`) | Builds answers with citations |
| **Observability** (`src/observability/`) | Streamlit Dashboard + evaluation |

### Pluggable Architecture

All core components use factory pattern with abstract base classes:
- **LLM**: `src/libs/llm/` - Azure, OpenAI, DeepSeek, Ollama, MiniMax
- **Embedding**: `src/libs/embedding/` - OpenAI, Azure, Ollama, MiniMax
- **Vector Store**: `src/libs/vector_store/` - Chroma (default)
- **Reranker**: `src/libs/reranker/` - Cross-Encoder, LLM

Configuration in `config/settings.yaml` controls which provider is used.

### Data Flow

```
Document → Loader (PDF→Markdown) → Splitter (recursive chunk) → Transform (metadata enrichment)
    → Dense Encoder (embedding) → Upsert (Chroma DB)
    → Sparse Encoder (BM25) → Upsert (BM25 index)

Query → Query Processor → Dense Retriever → Sparse Retriever → RRF Fusion → Rerank → Response Builder
```

### Key Files

- `src/mcp_server/server.py` - MCP protocol entry point
- `src/ingestion/pipeline.py` - Ingestion pipeline orchestration
- `src/core/query_engine/hybrid_search.py` - Hybrid search + RRF fusion
- `src/core/settings.py` - Configuration loader
- `src/libs/llm/llm_factory.py` - LLM provider factory
- `src/libs/evaluator/evaluator_factory.py` - Evaluator factory