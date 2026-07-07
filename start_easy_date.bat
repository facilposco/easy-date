@echo off
cd /d "%~dp0"
echo Starting Easy Date on http://localhost:8000
echo Main simulator: http://localhost:8000/simulador_v1.2.html
python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000
