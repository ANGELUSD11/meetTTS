#!/bin/bash
echo "==========================================="
echo "  Starting Google Meet AI Interpreter..."
echo "==========================================="

if [ ! -d "venv" ]; then
    echo "[!] Virtual environment not found. Creating one now..."
    python3 -m venv venv
fi

echo "[*] Activating virtual environment..."
source venv/bin/activate

echo "[*] Checking dependencies..."
pip install -r requirements.txt -q

echo "[*] Starting server on http://localhost:8000 ..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
