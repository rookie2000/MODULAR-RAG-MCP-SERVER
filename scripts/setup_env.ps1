param(
    [switch]$Recreate
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv is not installed. Install it first: https://docs.astral.sh/uv/getting-started/installation/"
}

if ($Recreate -and (Test-Path ".venv")) {
    Remove-Item -LiteralPath ".venv" -Recurse -Force
}

uv sync --extra dev
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Environment ready."
Write-Host "Run commands through uv, for example:"
Write-Host "  uv run python scripts/ingest.py --path tests/fixtures/sample_documents --dry-run"
Write-Host "  uv run pytest tests/unit -m unit"
