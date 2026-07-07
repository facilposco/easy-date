$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

Write-Host "Starting Easy Date on http://localhost:8000"
Write-Host "Main simulator: http://localhost:8000/simulador_v1.2.html"

python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000
