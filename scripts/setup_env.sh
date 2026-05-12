#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed. Install it first: https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

if [[ "${1:-}" == "--recreate" ]]; then
  rm -rf .venv
fi

uv sync --extra dev

cat <<'EOF'

Environment ready.
Run commands through uv, for example:
  uv run python scripts/ingest.py --path tests/fixtures/sample_documents --dry-run
  uv run pytest tests/unit -m unit
EOF
