<# run_prod.ps1
PowerShell helper to start the backend in production mode using `run_prod.py`.
Sets sensible defaults for `BIND_HOST` and `PORT` and verifies `eventlet` availability.
Usage: Open an elevated PowerShell (if needed for firewall changes), then:
  .\run_prod.ps1
#>

param()

Push-Location -Path $PSScriptRoot

# Set defaults (override by setting env vars before calling this script)
if (-not $env:FLASK_ENV) { $env:FLASK_ENV = 'production' }
if (-not $env:BIND_HOST) { $env:BIND_HOST = '0.0.0.0' }
if (-not $env:PORT) { $env:PORT = '5000' }

Write-Host "Starting backend with FLASK_ENV=$env:FLASK_ENV, BIND_HOST=$env:BIND_HOST, PORT=$env:PORT"

# Activate virtualenv if present
$venvActivate = Join-Path $PSScriptRoot '.venv\Scripts\Activate.ps1'
if (Test-Path $venvActivate) {
    Write-Host 'Activating virtual environment...'
    & $venvActivate
}

# Check for eventlet
try {
    python -c "import eventlet; print('eventlet', eventlet.__version__)" 2>$null
    Write-Host 'eventlet is available.'
} catch {
    Write-Warning 'eventlet not found. Install with: pip install eventlet'
}

Start-Process -NoNewWindow -FilePath python -ArgumentList 'run_prod.py'

Pop-Location
