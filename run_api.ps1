# run_api.ps1
$ErrorActionPreference = "Stop"

Write-Host "Starting FastAPI Server..."
.\.venv\Scripts\uvicorn.exe api.main:app --host 0.0.0.0 --port 8000 --reload
