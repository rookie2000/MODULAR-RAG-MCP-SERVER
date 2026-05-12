# Isolated Development Environment

This project uses `uv` to keep dependencies inside a project-local `.venv` directory. Do not run `pip install -e ".[dev]"` in your global Python environment.

## Setup

From the repository root:

```powershell
.\scripts\setup_env.ps1
```

On macOS or Linux:

```bash
bash scripts/setup_env.sh
```

The setup command runs:

```bash
uv sync --extra dev
```

This creates `.venv/` and installs both runtime and development dependencies there.

## Run Commands

Use `uv run` so commands always use the isolated project environment:

```bash
uv run python main.py
uv run python scripts/ingest.py --path tests/fixtures/sample_documents --dry-run
uv run python scripts/query.py --query "这个文档讲了什么" --collection demo --verbose
uv run python scripts/start_dashboard.py --port 8501
uv run pytest tests/unit -m unit
uv run ruff check src tests
uv run mypy src
```

If the environment becomes inconsistent, recreate it:

```powershell
.\scripts\setup_env.ps1 -Recreate
```

Or on macOS/Linux:

```bash
bash scripts/setup_env.sh --recreate
```
