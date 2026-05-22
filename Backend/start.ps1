# MicroSkillHub — single server (API + frontend)
# Run from Backend folder:  .\start.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    py -3.13 -m venv venv
    .\venv\Scripts\python.exe -m pip install --upgrade pip
    .\venv\Scripts\python.exe -m pip install -r requirements.txt
}

if (-not (Test-Path ".\.env")) {
    Write-Host "ERROR: .env missing. Copy .env.example to .env and add Supabase keys."
    exit 1
}

function Test-LocalPortFree([int]$Port) {
    $inUse = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return -not $inUse
}

$candidates = @()
if ($env:PORT) { $candidates += [int]$env:PORT } else { $candidates += 8000, 8080, 8888 }

$port = $null
foreach ($p in $candidates) {
    if (Test-LocalPortFree $p) {
        $port = $p
        break
    }
    Write-Host "Port $p is busy, trying next..."
}

if (-not $port) {
    Write-Host "ERROR: No free port (tried: $($candidates -join ', '))."
    Write-Host "Stop other servers:  Get-NetTCPConnection -LocalPort 8000 | Select OwningProcess"
    Write-Host "Then:  Stop-Process -Id <PID> -Force"
    exit 1
}

Write-Host ""
Write-Host "  MicroSkillHub running at:  http://127.0.0.1:$port"
Write-Host "  API docs:                  http://127.0.0.1:$port/docs"
Write-Host ""
.\venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port $port
