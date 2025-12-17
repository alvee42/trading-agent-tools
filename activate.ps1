# Quick activation script for virtual environment (PowerShell)
# Run this in PowerShell: .\activate.ps1

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Schwab Trading Agent Tools" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run setup first:" -ForegroundColor Yellow
    Write-Host "  python -m venv venv"
    Write-Host "  venv\Scripts\Activate.ps1"
    Write-Host "  pip install -r requirements.txt"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

& venv\Scripts\Activate.ps1

Write-Host "=========================================" -ForegroundColor Green
Write-Host "Virtual environment activated!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your prompt should now show: (venv)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quick commands:" -ForegroundColor Yellow
Write-Host "  - Run Weather Agent:  python Weather_Tools\weather_tools.py --symbol ES --output pretty"
Write-Host "  - Test installation:  python test_installation.py"
Write-Host "  - Deactivate venv:    deactivate"
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
