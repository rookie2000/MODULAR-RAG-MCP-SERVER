# Repository Guidelines

## Project Structure & Module Organization

This Python 3.10+ project is a modular RAG MCP server. Core code lives under `src/`:

- `src/mcp_server/` exposes MCP entry points, protocol handling, and tools.
- `src/ingestion/` contains document ingestion, chunking, transforms, embeddings, and storage.
- `src/core/` contains shared types, settings, queries, responses, and tracing.
- `src/libs/` holds pluggable LLM, embedding, reranker, loader, splitter, vector store, and evaluator providers.
- `src/observability/` contains logging, evaluation runners, and the Streamlit dashboard.

Scripts are in `scripts/`, configuration and prompts in `config/`, and tests in `tests/unit/`, `tests/integration/`, `tests/e2e/`, and `tests/fixtures/`.

## Build, Test, and Development Commands

- `pip install -e ".[dev]"`: install the package with test, lint, and type-check tools.
- `python main.py`: run the MCP server entry point locally.
- `python scripts/ingest.py`: run ingestion using local configuration.
- `python scripts/query.py`: query the configured knowledge hub.
- `python scripts/start_dashboard.py`: launch the Streamlit dashboard.
- `pytest`: run the full test suite.
- `pytest tests/unit -m unit`: run fast unit tests only.
- `pytest -m "not llm"`: skip tests requiring live LLM services.
- `ruff check src tests`: lint imports, naming, and Python style.
- `mypy src`: run static type checks.

## Coding Style & Naming Conventions

Use 4-space indentation and type hints for public interfaces. Keep modules and functions in `snake_case`, classes in `PascalCase`, and constants in `UPPER_SNAKE_CASE`. When adding providers, follow the factory/base-class pattern: implement in `src/libs/<capability>/` and register through the matching factory. Ruff targets Python 3.10 with a 100-character line length; long-line linting is ignored.

## Testing Guidelines

Tests use `pytest`, `pytest-asyncio`, `pytest-mock`, and `pytest-cov`. Name files `test_*.py`, classes `Test*`, and functions `test_*`. Use unit tests for pure module behavior, integration tests for provider/storage interaction, and e2e tests for complete MCP, ingestion, dashboard, or recall workflows. Mark external-service tests with `llm`, `integration`, `e2e`, or `slow`.

## Commit & Pull Request Guidelines

Recent history uses short imperative or conventional-style subjects such as `add: CLAUDE.md` and `feat: Modular RAG MCP Server ...`. Keep commits focused. Pull requests should include a summary, test results, linked issues, and screenshots for dashboard/UI changes. Note configuration, credential, or provider changes explicitly.

## Security & Configuration Tips

Do not commit real credentials. Use `config/test_credentials.yaml.example` as a template and keep local secrets untracked. When changing prompts in `config/prompts/` or provider settings in `config/settings.yaml`, document runtime dependencies and update affected tests or fixtures.
