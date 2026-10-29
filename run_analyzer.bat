@echo off
title C-Drive Dormant Space Scope
color 0b
echo ========================================================
echo       C-Drive Dormant Space Scope - Starting Up...
echo ========================================================
echo.
echo Launching local server and presentation dashboard...
cd /d "%~dp0c_drive_analyzer"
python app.py
pause
