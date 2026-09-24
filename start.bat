@echo off
echo ===========================================
echo   Starting Google Meet AI Interpreter...
echo ===========================================

IF NOT EXIST "venv" (
    echo [!] Virtual environment not found. Creating one now...
    python -m venv venv
)

echo [*] Activating virtual environment...
call venv\Scripts\activate

echo [*] Checking dependencies...
pip install -r requirements.txt -q

echo [*] Starting server on http://localhost:8000 ...
uvicorn app.main:app --host 0.0.0.0 --port 8000

pause
