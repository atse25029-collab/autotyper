@echo off
title AutoTyper Pro Launcher
cd /d "%~dp0"

echo [AutoTyper Pro] Starting up...

REM Check for virtual environment
if not exist "venv\Scripts\python.exe" (
    echo [AutoTyper Pro] Virtual environment not found. Setting up...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Python is not installed or not in PATH. Please install Python 3.8+!
        pause
        exit /b %errorlevel%
    )
    echo [AutoTyper Pro] Installing dependencies...
    venv\Scripts\pip install -r requirements.txt
)

REM Run application with pythonw (or python)
echo [AutoTyper Pro] Launching application...
start "" "venv\Scripts\pythonw.exe" main.py
if %errorlevel% neq 0 (
    echo [AutoTyper Pro] Launching in console mode for diagnosis...
    venv\Scripts\python.exe main.py
    pause
)
