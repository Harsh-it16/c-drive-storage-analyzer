# C-Drive Dormant Space Scope - PowerShell Launcher
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "      C-Drive Dormant Space Scope - Starting Up...      " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $ScriptDir "c_drive_analyzer")

Write-Host "Launching Python application and opening browser..." -ForegroundColor Green
python app.py
