# Start Agent 8 Unified Portal in development mode
# Flask API on port 5001 + React Dev Server on port 3000

Write-Host "========================================"
Write-Host "Agent 8 - Development Mode"
Write-Host "========================================"
Write-Host ""

# Kill any existing processes on ports 5001 and 3000
Write-Host "Cleaning up old processes..."
$port5001 = Get-NetTCPConnection -LocalPort 5001 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | Get-Unique
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | Get-Unique

if ($port5001) { Stop-Process -Id $port5001 -Force -ErrorAction SilentlyContinue }
if ($port3000) { Stop-Process -Id $port3000 -Force -ErrorAction SilentlyContinue }

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "Starting Flask API (port 5001)..."
Push-Location $PSScriptRoot
$env:PYTHONDONTWRITEBYTECODE=1
Start-Process python -ArgumentList "-B app.py" -NoNewWindow
Start-Sleep -Seconds 3

Write-Host "Starting React Dev Server (port 3000)..."
Push-Location "$PSScriptRoot\clinical-dashboard"
Start-Process npm -ArgumentList "start" -NoNewWindow

Pop-Location

Write-Host ""
Write-Host "========================================"
Write-Host "Services started:"
Write-Host "  - Flask API:      http://localhost:5001"
Write-Host "  - React Frontend: http://localhost:3000"
Write-Host "========================================"
Write-Host ""
Write-Host "Close this window when done. Both services will stop."
