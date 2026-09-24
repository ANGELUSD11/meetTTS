#!/bin/bash
echo "=============================================="
echo "  Iniciando AI Google Meet Interpreter..."
echo "=============================================="
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
