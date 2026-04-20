# create_env.ps1
$ErrorActionPreference = "Stop"

Write-Host "Creating Virtual Environment..."
python -m venv .venv

Write-Host "Upgrading pip..."
.\.venv\Scripts\python.exe -m pip install --upgrade pip

Write-Host "Installing dependencies..."
.\.venv\Scripts\pip.exe install -r requirements.txt

Write-Host "Environment setup complete!"
