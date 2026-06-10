@echo off
title Warp
echo.
echo  Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  Python not found.
    echo  Download it at: https://python.org/downloads
    echo  Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
echo  Starting Warp...
echo.
python app.py
pause
