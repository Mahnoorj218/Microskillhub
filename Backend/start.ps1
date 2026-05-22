# MicroSkillHub — single server (API + frontend)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    py -3.13 -m venv venv
    .\venv\Scripts\python.exe -m pip install --upgrade pip
    .\venv\Scripts\python.exe -m pip install -r requirements.txt
}

if (-not (Test-Path ".\.env")) {
    Write-Host "Copy .env.example to .env and add your Supabase keys first."
    exit 1
}

$port = if ($env:PORT) { $env:PORT } else { "8000" }
Write-Host "Starting MicroSkillHub at http://127.0.0.1:$port"
.\venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port $port
